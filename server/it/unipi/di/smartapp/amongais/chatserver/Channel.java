package it.unipi.di.smartapp.amongais.chatserver;

import java.util.HashSet;
import java.util.Set;
import java.util.logging.Logger;

import it.unipi.di.smartapp.amongais.logging.LogUtil;

public class Channel {
	private static final String LOG_CHAT = "Chat";
	private String name;
	private Set<ChatHandler> registered;
	private Logger log;
	
	public Channel(String name) {
		this.name=name;
		this.registered=new HashSet<ChatHandler>();
		log=LogUtil.initLogger(LOG_CHAT, name);
	}
	
	public synchronized void join(ChatHandler ch) {
		registered.add(ch);
	}
	
	public synchronized void leave(ChatHandler ch) {
		registered.remove(ch);
		if (getMembersCnt()==0)
			Server.close(this);
	}
	
	public synchronized void post(ChatHandler ch,String msg) {
		log.info(ch.getName()+": "+msg);
		Set<ChatHandler> toRemove = new HashSet<ChatHandler>();
		for (ChatHandler c: registered) {
			if (c.isTerminated())
				toRemove.add(c);
			else
				c.send(name,ch.getName(),msg);
		}
		registered.removeAll(toRemove);
	}
	
	public synchronized int getMembersCnt() {
		return registered.size();
	}

	public String getName() {
		return name;
	}

	public void shutdown() {
		log.info("Closing");
		LogUtil.closeLogger(LOG_CHAT, name);
	}
}
