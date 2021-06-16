package it.unipi.di.smartapp.amongais.chatserver;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.Socket;

import it.unipi.di.smartapp.amongais.gameserver.Main;

public class ChatHandler implements Runnable {

	private Socket socket;
	private String name=null;
	private BufferedReader in;
	private PrintWriter out;
	private boolean terminated=false;

	public ChatHandler(Socket socket) throws IOException {
		this.socket=socket;
		in=new BufferedReader(new InputStreamReader(socket.getInputStream()));
		out=new PrintWriter(new OutputStreamWriter(socket.getOutputStream()));
	}
	
	public void run() {
		boolean done=false;
		try {
			while (!done && !terminated) {
				String req=in.readLine();
				if (req!=null)
					done=processLine(req);
				else
					done=true;
				}
		} catch (IOException e) {
			System.err.printf("IOException in %s\n",name);
			terminate();
		} finally {
			try { socket.close(); } catch (IOException e) {;}
		}
		socket=null;
		terminated=true;
		Server.leaving(this);
	}

	private boolean processLine(String req) throws IOException {
		String[] words=req.split(" ");
		if (words.length<2) {
			System.err.printf("Invalid command '%s' from %s, exiting.\n",req,name);		
			return true;
		}
		String cmd=words[0];
		if ("NAME".equals(cmd) && name==null) {
			name=words[1];
			Thread.currentThread().setName(name);
			if (name.equals("@vg") || name.equals(Main.CHAT_GAME_SERVER))	// Backdoor!
				socket.setSoTimeout(0);
		} else if (name!=null) {
			String chan=words[1];
			switch (cmd) {
			case "JOIN": doJoin(chan); break;
			case "LEAVE": doLeave(chan); break;
			case "POST": doPost(chan, req.substring(6+chan.length())); break;
			default: System.err.printf("Bad chat command from %s: %s\n",name,req); return true;
			}
		}
		return false;
	}

	private void doPost(String chan, String line) {
		Server.channel(chan).post(this,line);
	}

	private void doLeave(String chan) {
		Server.channel(chan).leave(this);
	}

	private void doJoin(String chan) {
		Server.channel(chan).join(this);		
	}

	public String getName() {
		return name;
	}

	public void send(String chname, String author, String msg) {
//		try {
			out.printf("%s %s %s\n",chname,author,msg);
			out.flush();
//		} catch (IOException e) {
//			terminate();
//		}
	}

	public boolean isTerminated() {
		return terminated;
	}
	
	public void terminate() {
		terminated=true;
	}
}
