package it.unipi.di.smartapp.amongais.gameserver;

import java.io.IOException;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.List;
import java.util.Map;
import java.util.Vector;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;
import java.util.logging.Logger;

import it.unipi.di.smartapp.amongais.logging.LogUtil;

public class Main {
	public static final String CHAT_GAME_SERVER = "@GameServer";
	private static final int PORT=8421;
	private static final int KEEPALIVE = 50000;
	private static final Logger LOG=Logger.getLogger(Main.class.getName());
	private static final Object chatLock = new Object();
	protected static final String GLOBALCHANNEL = "#GLOBAL";
	private static final String LOG_GAME = "Game";
	private static Socket chatSocket=null;
	private static PrintWriter chat=null;
	
	private static Map<String,Game> games=new ConcurrentHashMap<String,Game>();
	
	public static void main(String[] args) throws IOException {
		LOG.setLevel(Level.WARNING);
		
		Runtime.getRuntime().addShutdownHook(new Thread() {
			public void run() {	
				chat(GLOBALCHANNEL,"Shutting down.");
				Vector<String> toRemove=new Vector<String>();
				synchronized (games) {
					for (String g: games.keySet()) {
						System.err.println(games.get(g).getName());
						toRemove.add(g);
						// TODO it would be even better to make all games stale, then purgeStaleGames()
					}
					for (String g:toRemove)
						remGame(g);
				}
			}
		});
		
		new Thread() {
			public void run() {
				Thread.currentThread().setName("Chat heartbeat");
				while (true) {
					try {
						Thread.sleep(10*60*1000);  // sleep 10 mins
					} catch (InterruptedException e) {
						LOG.warning("Heartbeat thread unexpectedly interrupted.");
					}
					chat(GLOBALCHANNEL,"Server heartbeat - I am alive!");
					LOG.info(String.format("%d games open; %d loggers open\n",games.size(),LogUtil.getOpenLoggers().size()));
				}
			}
		}.start();
		
		ServerSocket ssocket=new ServerSocket(PORT);
		System.out.printf("Game Server started on port %d\n",PORT);
		chat(GLOBALCHANNEL,"Ready to accept connections.");
		while (true) {
			Socket socket=ssocket.accept();
			socket.setSoTimeout(KEEPALIVE);
			ClientHandler ch=new ClientHandler(socket);
			new Thread(ch).start();
			purgeStaleGames();
		}
	}

	private static void attemptOpenChat() {
		try {
			if (chatSocket==null || chatSocket.isClosed()) {
				chatSocket = new Socket("localhost",8422);		// TODO put in a property / cli arg / constant ?
				chat = new PrintWriter(chatSocket.getOutputStream());
				chat.println("NAME "+CHAT_GAME_SERVER);
			}
		} catch (IOException e) {
			LOG.warning("Attempted to open chat socket and failed.");
		}
	}
	
	public static void chat(String channel,String msg) { // cannot contain \n
		if (channel.contains("\n") || msg.contains("\n")) {
			System.err.printf("Illegal chat line: [%s] [%s]\n",channel,msg);
			return;
		}
		synchronized (chatLock) {
			attemptOpenChat();
			chat.printf("POST %s %s\n", channel, msg);
			chat.flush();
		}
	}

	private static void purgeStaleGames() {
		List<Game> toRemove=new Vector<Game>();
		synchronized (games) {
			for (Game g: games.values())
				if (g.isStale()) {
					LOG.warning("Going to remove stale game "+g.getName()+" from "+g.getOwner().toString());
					chat(GLOBALCHANNEL,"Purging stale game "+g.getName());
					for (Player p: g.allPlayers()) {
						g.remPlayer(p);
					}
					// g.getOwner().terminate();
					toRemove.add(g);
				}
			for (Game g: toRemove)
				remGame(g.getName());
		}
		return;
	}

	public static Game getGame(String gName) {
		synchronized (games) {
			return games.get(gName);
		}
	}
	public static void putGame(String gName, Game g) {
		synchronized (games) {
			if (games.containsKey(gName))
				throw new IllegalArgumentException("Attempted to store a pre-existing game");
			games.put(gName,g);	
			LogUtil.initLogger(LOG_GAME, gName);
		}
	}
	public static void remGame(String gName) {
		synchronized (games) {
			if (!games.containsKey(gName))
				throw new IllegalArgumentException("Attempted to remove a non-existing game");
			games.remove(gName);
		}
		chat(gName,"Game is being removed.");
		log(gName,"Removed");
		LogUtil.closeLogger(LOG_GAME, gName);
	}

	public static void log(String log, String msg) {
		Logger l=LogUtil.getLogger(LOG_GAME,log);
		l.log(Level.INFO, msg);
	}
}
