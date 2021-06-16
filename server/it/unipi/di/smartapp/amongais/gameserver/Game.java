package it.unipi.di.smartapp.amongais.gameserver;

import java.util.HashMap;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Vector;

import it.unipi.di.smartapp.amongais.gameserver.GameMap.Direction;

public class Game {
	private static final int ENERGY_TRAP_PENALTY = 50;
	private static final int ENERGY_RECHARGE_VALUE = 20;
	private static final int SCORE_CAPTURE_FLAG = 50;
	private static final int SCORE_KILL_ANY = 0;
	private static final int SCORE_KILL_ENEMY = 10;
	private static final int SCORE_DIE = 0;
	private static final int SCORE_WINNING_TEAM = 20;
	private static final int SCORE_SURVIVOR = 10;
	private static final int SCORE_SURVIVOR_IMPOSTOR = 15;
	private static final int SCORE_JUDGE_CORRECT = 2;
	private static final int SCORE_JUDGE_INCORRECT = -1;
	private static final int SCORE_ACCUSE_IMPOSTOR = 15;
	private static final int SCORE_ACCUSE_MATE = 0;
	private static final int SCORE_IMPOSTOR_CAUGHT = -5;
	private static final int MAX_TEAM_SIZE = 20;
	private static final long PERIOD_STALE = 15*60*1000;		// 15 minutes
	private static final long PERIOD_LOG_LOOK = 1*1000;			// 5 seconds
	private static final long PERIOD_LOG_STATUS = 1*1000;		// 5 seconds
	protected static final long PERIOD_EMERGENCY_MEETING = 15*1000; // 15 seconds
	protected static final long PERIOD_EMERGENCY_MEETING_COOLDOWN = 45*1000; // 45 seconds   
	private static final long PERIOD_COOLDOWN_SHOOT = 5*1000; // 5 seconds
	private static final long PERIOD_COOLDOWN_CATCH = 30*1000; // 30 seconds
	
	private String name;
	private GameState state=GameState.INVALID;
	private int size=32;
	private int width=1;
	private boolean balanced=false;
	private boolean training=false;
	private boolean species=false;
	private boolean chatlog=false;
	private GameMap map;
	private Vector<Player>[] teams=new Vector[2];
	private boolean[] meeting=new boolean[2];
	private Player creator;
	private ClientHandler owner;
	private long lastStateChange;
	private long lastLOOKLog;
	private long lastSTATUSLog;
	private long lastSTART;
	private long uniq=0;
	
	public Game(String name,Player creator, ClientHandler owner, String opts) {
		this.name=name;
		setState(GameState.CREATED);
		if (opts.contains("1"))
			size=32; // keep default
		else if (opts.contains("2"))
			size=64;
		else if (opts.contains("3"))
			size=128;
		if (opts.contains("Q"))
			width=1; // keep default
		else if (opts.contains("W"))
			width=2;
		if (opts.contains("B"))
			balanced=true;
		if (opts.contains("T"))
			training=true;
		if (opts.contains("S"))
			species=true;
		if (opts.contains("l"))
			chatlog=true;
			
		map=new GameMap(size,width);
		map.initTerrain();
		map.initThings();
		teams[0]=new Vector<Player>(MAX_TEAM_SIZE);
		teams[1]=new Vector<Player>(MAX_TEAM_SIZE);
		this.creator=creator;
		this.owner=owner;
		creator.setState(PlayerState.LOBBYOWNER);
		meeting[0]=false;
		meeting[1]=false;
	}
	
	public synchronized void openLobby() {
		if (getState()==GameState.CREATED) {
			setState(GameState.LOBBY);
			chat("Lobby opened.");
		} else
			throw new IllegalStateException("Attempted to open lobby in invalid state");
	}
	
	public synchronized Vector<Player> allPlayers() {
		Vector<Player> v=new Vector<Player>(24);
		v.addAll(teams[0]);
		v.addAll(teams[1]);
		return v;
	}

	/*
	public synchronized void addObserver(Player p) {
		p.setGame(this);
		p.setState(PlayerState.LOBBYGUEST);
		p.setTeam(0);
		p.setLoyalty(0);
		p.setCodeLetter('z');
		p.setEnergy(0);
		p.setPos(0, 0);
		p.setScore(0);
	}
	*/
	
	public synchronized void addPlayer(Player p) {
		if (!p.getState().canJoin()) {
			throw new IllegalStateException("Player cannot join"); // TODO this should kill the CH thread
		}
		if (getState()!=GameState.LOBBY) {
			throw new IllegalStateException("Game must be in open lobby"); // TODO this should kill the CH thread
		}
		p.setGame(this);
		if (p.getState()==PlayerState.CREATED)
			p.setState(PlayerState.LOBBYGUEST);
		if (species)
			if ("H".equals(p.getNature()) && teams[0].size()<MAX_TEAM_SIZE)
				p.setTeam(0);
			else if ("AI".equals(p.getNature()) && teams[1].size()<MAX_TEAM_SIZE)
				p.setTeam(1);
			else
				throw new IllegalStateException("Your team is full");
		else if (teams[0].size()<MAX_TEAM_SIZE && teams[1].size()<MAX_TEAM_SIZE)
			if (balanced) {
				if (teams[0].size()<=teams[1].size())
					p.setTeam(0);
				else
					p.setTeam(1);
			} else {
				p.setTeam((int) (Math.random()*2));
			}
		else if (teams[0].size()==MAX_TEAM_SIZE && teams[1].size()<MAX_TEAM_SIZE)
			p.setTeam(1);
		else if (teams[1].size()==MAX_TEAM_SIZE && teams[0].size()<MAX_TEAM_SIZE)
			p.setTeam(0);
		else
			throw new IllegalStateException("Both teams full");
		if (Math.random()<0.9)
			p.setLoyalty(p.getTeam());
		else
			p.setLoyalty(1-p.getTeam());
		p.setEnergy(Player.MAX_ENERGY);
		p.setScore(0);
		//p.setCodeLetter((char) (p.getTeam()*32+'A'+teams[p.getTeam()].indexOf(p)));
		p.setCodeLetter(allocFreeLetter(p));
		int x,y;
		do {
			if (p.getTeam()==0)
				x=(int)(Math.random()*width*size/4);
			else
				x=width*size-(int)(Math.random()*width*size/4);
			y=(int) (Math.random()*size);
		} while (!map.isFreeSpot(x, y));
		p.setPos(x, y);
		teams[p.getTeam()].add(p);
		chat(p.getName()+" joined the game.");
	}
	
	private char allocFreeLetter(Player p) {
		char letter=(char) (p.getTeam()*32+'A'-1);
		Vector<Player> team=teams[p.getTeam()];
		boolean taken;
		do {
			letter++; taken=false;
			for (int i=0;i<team.size();i++)
				if (team.get(i).getCodeLetter()==letter) {
					taken=true;	break;
				}
		} while (taken);
		return letter;
	}

	public synchronized void start(Player c) {
		if (getState()!=GameState.LOBBY)
			throw new IllegalStateException("Can only start while in lobby");
		if (c!=creator)
			throw new IllegalArgumentException("Only creator can start a game");
		if (teams[0].size()==0 || teams[1].size()==0)
			throw new IllegalStateException("Need two non-empty teams to start");
		for (Player p: allPlayers()) {
			if (p.getState().inLobby())
				p.setState(PlayerState.ACTIVE);
			else
				throw new IllegalStateException("Invalid player in lobby state while starting game");
		}
		setState(GameState.ACTIVE);
		lastSTART=System.currentTimeMillis();
		chat("Now starting!");
		new Thread() {
			public void run() {
				try {
					Thread.sleep(PERIOD_COOLDOWN_SHOOT);
				} catch (InterruptedException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
				chat("Hunting season open!");
			}
		}.start();
		new Thread() {
			public void run() {
				try {
					Thread.sleep(PERIOD_COOLDOWN_CATCH);
				} catch (InterruptedException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
				chat("You can now catch the flag!");
			}
		}.start();
		
	}
	
	public synchronized boolean canAct(Player p) {
		return allPlayers().contains(p) 
				&& p.getState()==PlayerState.ACTIVE
				&& !p.getNature().equals("O")
				&& this.isRunning();
	}
	
	public synchronized boolean move(Player p, char dir) {
		if (canAct(p)) {
			char target=map.getMap(p.getX(), p.getY(), dir);
			if (GameMap.isWalkable(target)) { // target tile walkable, move player
				Direction d=Direction.forSymbol(dir);
				if (GameMap.isTrap(target))
					p.subEnergy(ENERGY_TRAP_PENALTY);
				if (GameMap.isRecharge(target)) {
					p.addEnergy(ENERGY_RECHARGE_VALUE);
					map.consumeO(p.getX()+d.dx,p.getY()+d.dy);
				}
				p.setPos(p.getX()+d.dx, p.getY()+d.dy);
			} else if (GameMap.isMoveable(target)) {
				Direction d=Direction.forSymbol(dir);
				if (GameMap.isWalkable(map.getMap(p.getX()+d.dx, p.getY()+d.dy, dir))) {
					map.moveO(p.getX()+d.dx, p.getY()+d.dy,dir);
					p.setPos(p.getX()+d.dx, p.getY()+d.dy);
				}
			} else if (GameMap.isFlag(target) && System.currentTimeMillis()-lastSTART > PERIOD_COOLDOWN_CATCH) {
				if (GameMap.team(target)!=p.getTeam()) { // VICTORY for p
					victory(p);
					return true;
				}
			} 
		}
		// TODO: player could not act, i.e. did not JOIN.
		return false;
	}

	private synchronized void victory(Player p) {
		if (p.getLoyalty()==p.getTeam())
			p.addScore(SCORE_CAPTURE_FLAG,"capturing the flag");
		this.setState(GameState.FINISHED);
		int winner=p.getTeam();
		Vector<Player> all=allPlayers();
		Vector<Player> hs=new Vector<Player>();
		Vector<Player> ais=new Vector<Player>();
		for (Player r:all) (r.isHuman()?hs:ais).add(r);
		Vector <Player> small=(hs.size()<ais.size()?hs:ais);
		Vector <Player> big=(hs.size()<ais.size()?ais:hs);
		reshuffle(small);
		reshuffle(big);
		if (small.size()>8) small.setSize(8);
		big.setSize(small.size());
		small.addAll(big);
		// no Turing game for BoS
		if (species)
			small.clear();
		for (Player q: all) {
			if (q.getState()==PlayerState.ACTIVE) {
				q.addScore(SCORE_SURVIVOR,"surviving till the end");
				if (q.getTeam()!=q.getLoyalty())
					q.addScore(SCORE_SURVIVOR_IMPOSTOR,"surviving till the end AND being an impostor");
			}
			if (q.getLoyalty()==winner)
				q.addScore(SCORE_WINNING_TEAM,"being loyal to the winning team");
			for (Player r:small) {
				if (r==q)
					continue;
				String j=q.getJudgement(r.getName());
				if (j!=null)
					if (j.equals(r.getNature())) 
						q.addScore(SCORE_JUDGE_CORRECT,"judging correctly the nature of "+r.getName());
					else
						q.addScore(SCORE_JUDGE_INCORRECT,"judging incorrectly the nature of "+r.getName());
			}
		}
		
		chat("Game finished! "+p.getName()+" from team "+p.getTeam()+" won the game.");
		log("VICTORY",p.getTeam()+" "+p.getCodeLetter()+" "+p.getName());
		String chatline, logline;
		for (Player q:all) {
			chatline=String.format("(%d:%c) %-16s %10s %4d", q.getTeam(), q.getCodeLetter(), q.getName(),q.getState(),q.getScore());
			logline=String.format("symbol=%c name=%s team=%d status=%s score=%d", q.getCodeLetter(), q.getName(),q.getTeam(),q.getState(),q.getScore()); 
			chat(chatline);
			log("SCORES",logline);
		}
		chat("-----------------");
	}
	
	private <E> void reshuffle(Vector<E> v) {
		int s=v.size();
		for (int n=0;n<v.size();n++) {
			int i=(int)(Math.random()*s), j=(int)(Math.random()*s);
			E tmp=v.get(i);
			v.set(i,v.get(j));
			v.set(j, tmp);
		}
	}

	public synchronized boolean isRunning() {
		return getState()==GameState.ACTIVE
				&& teams[0].size()>0
				&& teams[1].size()>0;
	}

	public synchronized char[][] look() {
		char[][] m=map.getMap();
		for (int t=0;t<2;t++)
			for (Player p: teams[t])
				m[p.getY()][p.getX()]=p.getCodeLetter();
		return m;
	}

	public synchronized char shoot(Player p, char dir) {
		if (canAct(p) && canShoot(p)) {
			Direction d=Direction.forSymbol(dir);
			int x=p.getX(), y=p.getY();
			Player victim=null;
			chat(p.getName()+" shot "+dir);
			do {
				p.subEnergy(1);
				x+=d.dx; y+=d.dy;
				victim=playerAt(x,y);
			}	while (victim==null && p.getEnergy()>0 && map.canShootOver(map.getMap(x, y)));
			if (victim!=null && victim.getState()==PlayerState.ACTIVE) {
				chat(p.getName()+" hit "+victim.getName());
				victim.setState(PlayerState.KILLED);
				p.addScore(SCORE_KILL_ANY,"having shot "+victim.getName());
				victim.addScore(SCORE_DIE,"having been shot by "+p.getName());
				if (p.getTeam()!=victim.getTeam())
					p.addScore(SCORE_KILL_ENEMY,"having shot "+victim.getName()+" who was an enemy");
				return victim.getCodeLetter();
			} else {
				 return  map.getMap(x, y);
			}	
		} else {
			return '0';
		}		
	}

	private Player playerAt(int x, int y) {
		for (Player p:allPlayers())
			if (p.getX()==x && p.getY()==y)
				return p;
		return null;
	}

	private boolean canShoot(Player p) {
		char terrain=map.getMap(p.getX(), p.getY()); 
		return map.canShootFrom(terrain) && p.getEnergy()>0 && System.currentTimeMillis()-lastSTART>PERIOD_COOLDOWN_SHOOT;
	}

	public String getName() {
		return name;
	}

	public GameState getState() {
		return state;
	}

	public synchronized void remPlayer(Player p) {
		int team=p.getTeam();
		teams[team].remove(p);
		p.setState(PlayerState.LEFT);
		chat(p.getName()+" left the game.");
	}

	public ClientHandler getOwner() {
		return owner;
	}

	public void setCreator(Player p) {
		creator=p;
	}

	public int getSize() {
		return size;
	}

	private synchronized void setState(GameState state) {
		this.state = state;
		this.lastStateChange=System.currentTimeMillis();
	}
	public boolean isStale() {
		return System.currentTimeMillis()-lastStateChange > PERIOD_STALE;
	}

	public synchronized Player playerNamed(String name) {
		Vector<Player> allp=allPlayers();
		for (Player p: allp) 
			if (p.getName().equals(name))
				return p;
		return null;
	}
	
	public synchronized boolean hasPlayerNamed(String name) {
		return playerNamed(name)!=null;
	}
	
	public void chat(String msg) {
		Main.chat(name, msg);
	}
	
	public void log(String msg) {
		Main.log(name,msg);
		if (isTraining() && isChatlog()) {
			String ch=name+"-L";
			long t=System.currentTimeMillis();
			if (msg.contains("\n")) {
				String a[] = msg.split("\n");
				for (String m:a)
					Main.chat(ch,++uniq+" "+t+" "+m);
			} else
				Main.chat(ch,++uniq+" "+t+" "+msg);
		}
	}

	public void log(String tag, String msg) {
		log(tag+" "+msg);
	}
	
	public synchronized boolean needLookLog() {
		if (System.currentTimeMillis()-lastLOOKLog>PERIOD_LOG_LOOK) {
			lastLOOKLog=System.currentTimeMillis();
			return true;
		} else
			return false;
	}
	public synchronized boolean needStatusLog() {
		if (System.currentTimeMillis()-lastSTATUSLog>PERIOD_LOG_STATUS) {
			lastSTATUSLog=System.currentTimeMillis();
			return true;
		} else
			return false;
	}

	public synchronized boolean accuse(Player accuser, Player accused) {
		if (!isRunning())
			return false;
		if (!canAct(accuser))
			return false;
		if (accused.getTeam()!=accuser.getTeam())
			return false;
		if (accused.getState()!=PlayerState.ACTIVE)
			return false;
		accuser.setAccused(accused);
		if (meeting[accuser.getTeam()]==false) {
			if (System.currentTimeMillis()-accuser.getLastEmergencyCallTime()<PERIOD_EMERGENCY_MEETING_COOLDOWN)
				return false;
			accuser.setLastEmergencyCallTime(System.currentTimeMillis());
			chat("EMERGENCY MEETING! Called by "+accuser.getName());
			log("IMPOSTOR","Team "+accuser.getTeam()+": Call meeting.");
			meeting[accuser.getTeam()]=true;
			final Game thisGame=this;
			final int thisTeam=accuser.getTeam();
			new Thread() {
				public void run() {
					try {
						Thread.sleep(PERIOD_EMERGENCY_MEETING);
					} catch (InterruptedException e) {
						System.err.println("Unexpected interrup on meeting thread!");
					}
					thisGame.endMeeting(thisTeam);
				}
			}.start();
		}
		chat(accuser.getName()+" accuses "+accused.getName());
		return true;
	}

	protected synchronized void endMeeting(int team) {
		meeting[team]=false;
		if (!isRunning())
			return;
		Map<Player,Integer> tally=new HashMap<Player,Integer>();
		Vector <Player> mates=teams[team];
		int n=0;
		for (Player p: mates) {
			if (p.getState()==PlayerState.ACTIVE) { // only votes of players ALIVE at the end of the meeting are counted
				n++;
				if (p.getAccused()!=null) {
					if (!tally.containsKey(p.getAccused()))
						tally.put(p.getAccused(), 1);
					else
						tally.put(p.getAccused(),tally.get(p.getAccused())+1);
				}
			}
		}
		double quorum=n/2.0;
		Player victim=null;
		chat("EMERGENCY MEETING for team "+team+" ended.");
		for (Entry<Player, Integer> e: tally.entrySet()) {
			chat(String.format("   %2d %s", e.getValue(),e.getKey().getName()));
			if (e.getValue()>quorum) {
				victim=e.getKey();
				break;
			}
		}
		if (victim==null) {
			chat("EMERGENCY MEETING miscarriage. No majority on impostor.");
			log("IMPOSTOR","Team "+team+": No majority");
		} else {
			boolean wasImpostor=victim.getLoyalty()!=victim.getTeam();
			chat("EMERGENCY MEETING condamned "+victim.getName()+", who was "+(!wasImpostor?"NOT ":"")+"an impostor!");
			log("IMPOSTOR","Team "+team+": Expelling "+victim.getName());
			victim.setState(PlayerState.KILLED);
			for (Player p:mates) {
				if (p.getAccused()==victim) {
					p.addScore(wasImpostor?SCORE_ACCUSE_IMPOSTOR:SCORE_ACCUSE_MATE,"having voted "+victim.getName()+" as impostor");
				}
				p.setAccused(null);
			}
			victim.addScore(SCORE_DIE,"being condamned as impostor");
			if (wasImpostor) victim.addScore(SCORE_IMPOSTOR_CAUGHT,"being caught as impostor");
		}
	}

	public boolean isTraining() {
		return training;
	}

	public boolean isChatlog() {
		return chatlog;
	}

	public int getWidth() {
		return width;
	}
	
}
