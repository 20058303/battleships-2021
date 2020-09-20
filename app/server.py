import backoff
import queue
import redis
import threading
import uuid
import log
from battleships_pb2 import Attack, Response, Status
from battleships_pb2_grpc import BattleshipsServicer
from game import Game
from message import Message

logger = log.get_logger(__name__)


class Battleship(BattleshipsServicer):
    OpenGames = 'openGames'

    def __init__(self, redis_host, redis_port='6379', db=0):
        """Create a Battleship (server) instance.

        :param redis_host: Hostname of Redis instance
        :param redis_port: Port of Redis instance
        :param db: Database to use within Redis instance
        """
        self.__r = redis.Redis(host=redis_host, port=redis_port, db=db)
        self.__q = queue.Queue()
        self.__e = threading.Event()
        self.__e.set()

        self.__stream = None

    def __enter__(self):
        """Entry point for the context manager.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit point for the context manager.

        Closes any open connections.
        """
        self.close()

    def Game(self, request_iterator, context):
        """This method is the implementation of the gRPC Game service.
        When connected, this provides the main functionality of the
        Battleship game.
        """
        self.__stream = request_iterator

        request = self.recv()
        if not request.HasField('join'):
            logger.error('Not a join message!')
            return

        player_id = request.join.id
        if player_id == '':
            logger.error('Player message does not contain valid ID')
            return

        logger.info(f'Player {player_id} is attempting to join')

        game, is_new = self.find_game()

        logger.info(f'Connecting to game {game.id}. '
                    f'New? {"Yes" if is_new else "No"}')
        logger.info('Setting up server to start receiving PubSub messages')

        pubsub_thread = self.subscribe_redis(game, player_id)
        if not self.connect_game(game, player_id, is_new):
            logger.error('Unable to connect to a game!')
            return

        game_thread = self.subscribe_grpc(game, player_id)

        while self.is_running:
            yield self.get()

        game_thread.join()
        pubsub_thread.stop()
        self.close_open_game(game)

    def recv(self):
        """Receive a gRPC message.

        :return: gRPC message that was received
        """
        return next(self.__stream)

    def send(self, response):
        """Send a gRPC message.

        :param response: Response to send to the client
        """
        self.__q.put_nowait(response)

    def get(self):
        """Get next message from the queue.

        :return: Next message in queue
        """
        return self.__q.get()

    @property
    def is_running(self):
        """Is the game still running?

        :return: True if running, False otherwise
        """
        return self.__e.is_set()

    def stop(self):
        """Stop the game from running.
        """
        self.__e.clear()

    def ping_redis(self):
        """Ping a Redis instance.

        :return: True if connection to instance established, False otherwise
        """
        @backoff.on_exception(backoff.expo, redis.exceptions.ConnectionError)
        def __ping_redis():
            """Convenience function that does the actual Redis PING.
            """
            return self.__r.ping()

        try:
            return __ping_redis()
        except redis.exceptions.ConnectionError:
            return False

    @property
    def redis_conn(self):
        """Return Redis client as a property.
        """
        return self.__r

    def close(self):
        """Close connections, like the connection to the Redis instance.
        """
        self.__r.close()

    def subscribe_grpc(self, game, player_id):
        """Create a thread that handles incoming gRPC requests.

        :param game: Game to handle requests for
        :param player_id: Player this game server is handling
        :return: Thread handling the gRPC requests
        """
        def get_grpc_handler():
            def handle_grpc():
                return self.handle_grpc(game, player_id)
            return handle_grpc

        game_thread = threading.Thread(target=get_grpc_handler())
        game_thread.daemon = True
        game_thread.start()
        return game_thread

    def handle_grpc(self, game, player_id):
        """Handle actual gRPC requests.

        :param game: Game to handle
        :param player_id: Id of player this game server is handling
        """
        while True:
            request = self.recv()

            if request.HasField('move'):
                # It must be my move if we have to handle an Attack
                if game.my_turn:
                    move = request.move.vector
                    msg = Message(Message.ATTACK, player_id, move)
                    self.publish(game.id, msg)
                else:
                    logger.error('Got {move} request but not my turn!')

            elif request.HasField('report'):
                # It must not be my move if we have to handle a Report
                if not game.my_turn:
                    state = request.report.state
                    if state == Status.State.DEFEAT:
                        msg = Message(Message.LOST, player_id, '')
                    else:
                        msg = Message(Message.STATUS, player_id, str(state))

                    self.publish(game.id, msg)
                else:
                    logger.error('Got {report} request but it is my turn!')

            else:
                logger.error('Received an unknown message type!')

    def publish(self, channel, message):
        """Publish a message to Redis PubSub on a certain channel.

        :param channel: Channel to use
        :param message: Message to publish
        """
        self.__r.publish(channel, message)

    def subscribe_redis(self, game, player_id):
        """Subscribe to game.id channel but in a separate thread.
        The handler that is used for the pubsub message is called
        handle_pubsub, which is a method of this class.

        :param game: Game of which the ID is used to subscribe
        :param player_id: ID of player this game server is handling
        :return: Thread that the handler is running in
        """
        def get_pubsub_handler():
            def handle_pubsub(msg):
                return self.handle_pubsub(msg, game, player_id)
            return handle_pubsub

        p = self.__r.pubsub(ignore_subscribe_messages=True)
        p.subscribe(**{game.id: get_pubsub_handler()})
        thread = p.run_in_thread(sleep_time=0.001)
        return thread

    def handle_pubsub(self, msg, game, player_id):
        """Handle published messages from Redis PubSub.
        :param msg: PubSub message to handle
        :param game: Game for which to handle messages
        :param player_id: Player for which we're receiving messages
        """
        message = Message.recreate(msg)
        message_type = message.type
        if message_type == Message.BEGIN:
            response = Response(turn=Response.State.BEGIN)
            self.send(response)

            if message.player == player_id:
                # Stop this player's turn (this will start other player's turn)
                message = Message(Message.STOP_TURN, player_id, '')
                self.publish(game.id, message)

        elif message_type == Message.STOP_TURN:
            logger.info(f'Received STOP_TURN from player {message.player}')
            if message.player == player_id:
                game.end_turn()
                turn = Response.State.STOP_TURN
            else:
                logger.info(f'Starting turn for player {player_id}')
                game.start_turn()
                turn = Response.State.START_TURN

            self.send(Response(turn=turn))

        elif message_type == Message.ATTACK:
            logger.info(f'Received ATTACK from player {message.player} '
                        f'with vector {message.data}')

            if message.player != player_id:
                self.send(Response(move=Attack(vector=message.data)))

        elif message_type == Message.STATUS:
            state = "HIT" if message.data == Status.State.HIT else "MISS"
            logger.info(f'Received STATUS from player {message.player} with '
                        f'state {state}')

            if message.player == player_id:
                self.send(Response(move=Status(state=message.data)))

                # Stop this player's turn (this will start other player's turn)
                message = Message(Message.STOP_TURN, player_id, '')
                self.publish(game.id, message)

        elif message_type == Message.LOST:
            logger.info(f'Received LOST from player {message.player}')
            turn = Response.State.LOST
            if message.player == player_id:
                turn = Response.State.WIN

            self.send(Response(turn=turn))
            self.stop()

    def ensure_subscribers(self, game, n):
        """Ensure that {n} listeners are subscribed to the id of the
        game passed in as a parameter.

        :param game: Game of which the ID is checked
        :param n: The number of subscribers we're expecting
        """
        values = self.__r.pubsub_numsub(game.id)
        if len(values) < 1:
            return False

        _, nsub = values[0]
        return n == nsub

    def connect_game(self, game, player_id, is_new):
        """Join an existing game or advertise this one as open if game
        is not yet in progress.

        :param game: Game
        :param player_id: ID of player
        :param is_new: True if game is new, False otherwise
        """
        if is_new:
            return self.add_open_game(game)

        if not self.ensure_subscribers(game, 2):
            return False

        msg = Message(Message.BEGIN, player_id, '')
        self.publish(game, msg)
        return True

    def find_game(self):
        """Try to find an open game in Redis or create a new game if
        none found.

        :return: A tuple containing a Game object and a flag is_new
        which indicates that a new game was created.
        """
        b_game_id = self.__r.rpop(self.OpenGames)

        # b_game_id is None if no open game found
        is_new = b_game_id is None
        if is_new:
            logger.info('Could not find open game, creating new one')
            game_id = str(uuid.uuid4())
        else:
            game_id = b_game_id.decode('utf-8')

        return Game(game_id), is_new

    def add_open_game(self, game):
        """Add an open game to the Redis instance so it can be discovered.

        :param game: Game to be advertised
        :return: True if successful, False otherwise
        """
        logger.info(f'Adding open game {game.id}')
        return self.__r.lpush(self.OpenGames, game.id)

    def close_open_game(self, game):
        """Remove an open game from the Redis instance so it can no longer
        be discovered.

        :param game: Game to be closed
        """
        logger.info(f'Closing open game {game.id}')
        return self.__r.lrem(self.OpenGames, 1, game.id)
