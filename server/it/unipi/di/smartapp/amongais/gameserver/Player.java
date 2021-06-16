package it.unipi.di.smartapp.amongais.gameserver;

import java.util.HashMap;
import java.util.Map;

public class Player {
	public static final int MAX_ENERGY = 256; // TODO: Maybe move in Game?
	private String name;
	private String nature;
	private String role;
	private String[] userInfo;
	private PlayerState state;
	private Game game;
	private ClientHandler owner;
	private int x,y;
	private int energy;
	private int score;
	private int team;
	private int loyalty;
	private char codeLetter;
	private Map<String,String> turing=new HashMap<String, String>(20);
	private Player accused=null;
	private long lastMeetingCall=0;
	
	public Player(String name) {
		this.name=name;
		this.setState(PlayerState.CREATED);
	}
	
	public Player(String name, String nature, String role, String[] userInfo) {
		this.name=name;
		this.nature=nature;
		this.role=role;
		this.userInfo=userInfo;
		this.setState(PlayerState.CREATED);
	}

	public ClientHandler getOwner() {
		return owner;
	}

	public void setOwner(ClientHandler owner) {
		this.owner = owner;
	}

	public PlayerState getState() {
		return state;
	}

	public void setState(PlayerState state) {
		this.state = state;
	}
	
	public void setPos(int x,int y) {
		this.setX(x); this.setY(y);
	}

	public Game getGame() {
		return game;
	}

	public void setGame(Game game) {
		this.game = game;
	}

	public int getX() {
		return x;
	}

	public void setX(int x) {
		this.x = x;
	}

	public int getY() {
		return y;
	}

	public void setY(int y) {
		this.y = y;
	}

	public int getEnergy() {
		return energy;
	}

	public void setEnergy(int energy) {
		if (energy<0) energy=0;
		if (energy>MAX_ENERGY) energy=MAX_ENERGY;
		this.energy = energy;
	}

	public void addEnergy(int increment) {
		setEnergy(this.energy +increment);
	}

	public void subEnergy(int decrement) {
		setEnergy(this.energy-decrement);
	}

	public int getScore() {
		return score;
	}

	public void setScore(int score) {
		this.score = score;
	}

	public int getTeam() {
		return team;
	}

	public void setTeam(int team) {
		this.team = team;
	}

	public int getLoyalty() {
		return loyalty;
	}

	public void setLoyalty(int loyalty) {
		this.loyalty = loyalty;
	}

	public char getCodeLetter() {
		return codeLetter;
	}

	public void setCodeLetter(char codeLetter) {
		this.codeLetter = codeLetter;
	}

	public String getName() {
		return name;
	}
	
	public String getNature() {
		return nature;
	}

	public void addScore(int score) {
		setScore(getScore()+score);		
	}

	public void addScore(int score,String reason) {
		addScore(score);
		if (game!=null)
			game.log("SCORING", "Awarded "+score+" to "+name+" for "+reason);
	}
	
	public void judge(String player,String nature) {
		turing.put(player, nature);
	}
	
	public String getJudgement(String player) {
		return turing.get(player);
	}

	public boolean isHuman() {
		return nature.equals("H");
	}
	
	public String toString() {
		return getName()+"@"+game.getName()+" "+getNature();
	}

	public Player getAccused() {
		return accused;
	}

	public void setAccused(Player accused) {
		this.accused = accused;
	}

	public long getLastEmergencyCallTime() {
		return lastMeetingCall;
	}

	public void setLastEmergencyCallTime(long currentTimeMillis) {
		lastMeetingCall=currentTimeMillis;
	}
}
