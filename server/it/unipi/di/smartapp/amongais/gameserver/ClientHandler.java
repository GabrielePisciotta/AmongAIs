package it.unipi.di.smartapp.amongais.gameserver;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.net.Socket;
import java.util.Arrays;
import java.util.logging.Level;
import java.util.logging.Logger;

public class ClientHandler implements Runnable {
	private Socket sock;
	private BufferedReader in;
	private PrintWriter out;
	private long lastCmdTime=System.currentTimeMillis()-MINCMDTIME;
	private long prevCmdTime=lastCmdTime;
	private String lastReq;
	private Player me;
	private static final Logger LOG=Logger.getLogger(ClientHandler.class.getName());
	private static final int MINCMDTIME=300;
	
	public ClientHandler(Socket socket) {
		LOG.setLevel(Level.WARNING);
		sock=socket;
		LOG.info("Serving a client from "+socket.getRemoteSocketAddress());
	}
	public void run() {
		Thread.currentThread().setName(toString());
		boolean done=false;
		try {
			in=new BufferedReader(new InputStreamReader(sock.getInputStream()));
			out=new PrintWriter(new OutputStreamWriter(sock.getOutputStream()));
			while (!done) {
				String req=in.readLine();
				lastReq=req;
				if (req!=null)
					done=processCmd(req);
				else
					done=true;
			}
		} catch (IOException e) {
			LOG.log(Level.WARNING,"EXC  P={0} T={1} Exc={2}",new Object[] {me!=null?me.getName():"-",Thread.currentThread().getName(),e});
			if (me!=null && me.getGame()!=null) {
				me.getGame().chat(me.getName()+" was disconnected. Goodbye cruel world!");
				log("PLAYER-DISCONNECTED",me.getName()+" was disconnected");
			}
		} finally {
			try {
				sock.close();
			} catch (IOException e) {
				LOG.log(Level.WARNING,"EXC  P={0} T={1} Exc={2}",new Object[] {me!=null?me.getName():"-",Thread.currentThread().getName(),e});
			} finally {
				sock=null;
			}
		}
	}
	
	private void response(boolean ok, int code, String text) {
		LOG.log(Level.INFO,"IN   P={0} T={1} Req=[{2}] Ok={3}",new Object[] {me!=null?me.getName():"-",Thread.currentThread().getName(),lastReq,ok});
		if (ok) {
			out.printf("OK %s\n",text);
			if (text.indexOf("\n")>=0) {
				String a[] = text.split("\n");
				text=a[0];
			}
			log("RESPONSE-TO","OK "+text);
		} else {
			out.printf("ERROR %d %s\n",code,text);
			log("RESPONSE-TO","ERROR "+code+" "+text);
		}
		out.flush();
	}
	
	private void log(String tag, String msg) {
		if (me!=null && me.getGame()!=null) {
			me.getGame().log(tag,(me.getName()!=null?me.getName():"unnamed")+" "+msg);
		}
		
	}
	private boolean processCmd(String req) {
		long curTime=System.currentTimeMillis();
		long elapsedTime=curTime-lastCmdTime;
		prevCmdTime = lastCmdTime;
		lastCmdTime=curTime;
		long timeslot=500;
		if (me!=null && "AI".equals(me.getNature()))
			timeslot=300;
		if (me!=null && "H".equals(me.getNature()))
			timeslot=150;
		if (me!=null && "O".equals(me.getNature()))
			timeslot=50;
		if (me!=null && me.getGame()!=null && me.getGame().isTraining())
			timeslot=5;
		log("REQUEST-FROM",req);
		try {
			/*
			if (me.isHuman() && (words[1].equals("LOOK") || words[1].equals("STATUS"))) {
				;
			} else 
			*/
			String[] words=req.split(" ");
			if ( elapsedTime < timeslot) {
				response(false,401,"Too fast");
				return true;
			}
			if (words[0].equals("NEW"))
					return processNEW(words);
			else {
				String gName=words[0];
				Game game = Main.getGame(gName);
				if (game==null) {
					response(false,404,"Game not found");
					return false;
				}
				String cmd=words[1];
				String[] params=Arrays.copyOfRange(words, 2, words.length);
				switch (cmd) {
				// No-op protocol
				case "NOP": return processNOP(game,params);
				// Boot protocol
				case "JOIN": boolean b=processJOIN(game,params); log("REQUEST-FROM",req); return b;
				case "START": return processSTART(game,params);
				// Actions protocol
				case "LOOK": return processLOOK(game,params);
				case "MOVE": return processMOVE(game,params);
				case "SHOOT": return processSHOOT(game,params);
				case "STATUS": return processSTATUS(game,params);
				// Social protocol
				case "ACCUSE": return processACCUSE(game,params);
				case "JUDGE": return processJUDGE(game,params);
				case "LEAVE": return processLEAVE(game,params);
				default: 
					response(false,500,"Unknown command");
					return false;
				}
			}
		} catch (Exception e) {
			response(false,502,e.getMessage());
			return false;
		}
	}
	private boolean processNEW(String[] words) {
		String gName=words[1];
		String opts=(words.length>2)?words[2]:"";
		Player p=new Player("unnamed");
		p.setOwner(this);
		me=p;
		Game game=new Game(gName, p, this,opts);
		Main.putGame(gName, game);
		game.openLobby();
		response(true,0,"Created");
		return false;
	}
	private boolean processLEAVE(Game game, String[] params) {
		game.remPlayer(me);
		response(true,0,"Left game");
		return true;
	}
	private boolean processACCUSE(Game game, String[] params) {
		String player=params[0];	// would fail if wrong params
		Player accused=game.playerNamed(player);
		if (accused==null) {
			response(false,410,"Player "+player+" not in game.");
			return false;
		}
		if (game.accuse(me,accused))
			response(true,0,"Noted.");
		else
			response(false,411,"Accuse failed.");
		return false;
	}
	private boolean processJUDGE(Game game, String[] params) {
		String player=params[0], nature=params[1];	// would fail if wrong params
		if (!game.hasPlayerNamed(player))
			response(false,410,"Player "+player+" not in game.");
		else {
			me.judge(player, nature);
			response(true,0,"Noted.");
		}
		return false;
	}
	private boolean processSTATUS(Game game, String[] params) {
		StringWriter sw=new StringWriter();
		PrintWriter pw=new PrintWriter(sw);
		pw.printf("LONG\n");
		pw.printf("GA: name=%s state=%s size=%d ratio=%s\n",game.getName(),game.getState().toString(),game.getSize(),game.getWidth()==2?"W":"Q");
		if (me!=null && me.getCodeLetter()!='\0')
			pw.printf("ME: symbol=%c name=%s team=%d loyalty=%d energy=%d score=%d\n",me.getCodeLetter(), me.getName(), me.getTeam(), me.getLoyalty(), me.getEnergy(), me.getScore());
		for (Player p:game.allPlayers()) {
			pw.printf("PL: symbol=%c name=%s team=%d x=%d y=%d state=%s\n", p.getCodeLetter(), p.getName(),p.getTeam(),p.getX(),p.getY(),p.getState());
		}
		pw.printf("«ENDOFSTATUS»");
		if (game.needStatusLog()) log("STATUS",sw.toString());

		response(true,0,sw.toString());
		return false;
	}
	private boolean processSHOOT(Game game, String[] params) {
		char dir=params[0].charAt(0); // TODO would fail on empty string
		char hit=game.shoot(me,dir);
		if (hit=='0')
			response(false,406,"Cannot shoot");
		else
			response(true,0,new String(new char[] {hit}) );
		return false;
	}
	private boolean processMOVE(Game game, String[] params) {
		if (params[0].length()<1) {
			response(false,505,"Need a direction in MOVE");
			return false;
		}
		char dir=params[0].charAt(0); // TODO would fail on empty string
		int x=me.getX(), y=me.getY();
		game.move(me, dir);
		response(true,0,(x==me.getX() && y==me.getY())?"blocked":"moved");
		return false;
	}
	private boolean processLOOK(Game game, String[] params) {
		char[][] map=game.look();
		StringBuffer sb=new StringBuffer(128*128);
		sb.append("LONG\n");
		for (int i=0;i<map.length;i++) { 
			sb.append(map[i]);
			sb.append("\n");
		}
		sb.append("«ENDOFMAP»");
		if (game.needLookLog()) log("MAP",sb.toString());

		response(true,0,sb.toString());
		return false;
	}
	private boolean processSTART(Game game, String[] params) {
		game.start(me);
		response(true,0,"Game started");
		return false;
	}
	private boolean processJOIN(Game game, String[] params) {
		Player p;
		synchronized (game) {						// test if player name available + add player to the game must be atomic
			if (game.hasPlayerNamed(params[0])) {
				response(false,410,"Player name already taken in this game");
				return false;
			} 
			p=new Player(params[0],params[1],params[2],Arrays.copyOfRange(params, 3, params.length));
			p.setOwner(this);
			if (!p.getNature().equals("O"))
				game.addPlayer(p); // This will complete initialization of p
			else {
				p.setGame(game);
			}
		}
		Thread.currentThread().setName(p.toString());
		me=p;
		if (game.getOwner()==this) {
			game.setCreator(p);
			p.setState(PlayerState.LOBBYOWNER);
		}
		if (p.getNature().equals("O"))
			response(true,0,"observer");
		else
			response(true,0,"team="+p.getTeam()+" loyalty="+p.getLoyalty());
		return false;
	}
	private boolean processNOP(Game game, String[] params) {
		if (System.currentTimeMillis()-prevCmdTime <10000) { 
			response(false,510,"Don't abuse NOPs!");
			LOG.log(Level.WARNING,"Abuser @"+sock.getRemoteSocketAddress());
			return true;
		} else {
			response(true,0,"No operation");
			return false;
		}
	}
	
	public String toString() {
		return "CH for "+
				((sock!=null)?sock.getRemoteSocketAddress():"no-socket")+
				((me!=null)?" as "+me.getName()+" in game "+((me.getGame()!=null)?me.getGame().getName():"no-game"):"no-name");
	}
	
	
}
