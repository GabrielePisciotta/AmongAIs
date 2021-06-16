package it.unipi.di.smartapp.amongais.chatserver;

import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Vector;

public class Server {
	private static final int PORT = 8422;
	private static final int KEEPALIVE = 15*60*1000; // 15 mins
	private static Map<String,Channel> channels = new HashMap<String,Channel>();

	public static void main(String[] args) throws IOException {
		@SuppressWarnings("resource")
		ServerSocket ssocket=new ServerSocket(PORT);
		System.out.printf("Chat Server started on port %d\n",PORT);
		while (true) {
			Socket socket=ssocket.accept();
			socket.setSoTimeout(KEEPALIVE);
			ChatHandler ch=new ChatHandler(socket);
			new Thread(ch).start();
			// TODO from time to time, purge channels
		}
	}

	public static synchronized Channel channel(String chan) {
		if (channels.containsKey(chan))
			return channels.get(chan);
		else {
			Channel ch=new Channel(chan);
			channels.put(chan, ch);
			System.out.printf("%d channels open.\n",channels.size());
			return ch;
		}
	}
	
	public static synchronized void close(Channel ch) {
		if (ch.getMembersCnt()==0) {
			channels.remove(ch.getName());
			ch.shutdown();
		}
	}

	public static synchronized void leaving(ChatHandler ch) {
		List<Channel> toLeave = new Vector<Channel>();
		for (Entry<String, Channel> e: channels.entrySet()) {
			toLeave.add(e.getValue());
		}
		for (Channel c: toLeave)
			c.leave(ch);
	}
}
