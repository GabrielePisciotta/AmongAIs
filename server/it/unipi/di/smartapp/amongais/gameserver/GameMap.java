package it.unipi.di.smartapp.amongais.gameserver;

public class GameMap {
	private char[][] terrain;
	private char[][] things;
	private int size;
	private int width;
	
	public enum Terrain {
		VOID('?'),GRASS('.'), WALL('#'),RIVER('~'),OCEAN('@'),TRAP('!'); 
		private char symbol;
		private Terrain(char symbol) {
			this.symbol=symbol;
		}
	}

	public enum Thing {
		NOTHING(' '), BATTERY('$'),OBSTACLE('&'),FLAG1('X'),FLAG2('x'); 		
		private char symbol;
		private Thing(char symbol) {
			this.symbol=symbol;
		}
	}
	
	public enum Direction {
		NORTH('N',0,-1), EAST('E',+1,0), SOUTH('S',0,+1),WEST('W',-1,0);
		public char symbol;
		public int dx,dy;
		private Direction(char symbol,int dx, int dy) {
			this.symbol=symbol;
			this.dx=dx;
			this.dy=dy;
		}
		public static Direction forSymbol(char dir) {
			switch (dir) {
			case 'N': return NORTH;
			case 'E': return EAST;
			case 'S': return SOUTH;
			case 'W': return WEST;
			default: throw new IllegalArgumentException("Invalid Direction "+dir);
			}
		}
	}

	public GameMap(int size) {
		this(size,1);
	}
	
	public GameMap(int size, int width) {
		this.size=size;
		this.width=width;
		terrain = new char[size][size*width];
		things = new char[size][size*width];
	}

	public void initTerrain() {
		// Grass, grass everywhere
		for (int i=0;i<size*width;i++)
			for (int j=0;j<size;j++)
				setT(i,j,Terrain.GRASS);
		// Mountain (wall) ranges
		int nseeds=(int) (2+Math.random()*width*Math.sqrt(size));
		double growth=1.0-(1.0/size);
		for (int i=0;i<nseeds;i++) {
			int x=(int)(Math.random()*size*width);
			int y=(int)(Math.random()*size);
			while (Math.random()<growth) {
				setT(x,y,Terrain.WALL);
				x += randomStep();
				y += randomStep(-2,2);
			}
		}
		// Rivers
		nseeds=(int) (Math.random()*3*width);
		growth=1.0-(1.0/size);
		int dir=randomStep(0,1);
		for (int i=0;i<nseeds;i++) {
			int x=(int)(Math.random()*size*width);
			int y=dir*size;

			while (Math.random()<growth) {
				setT(x,y,Terrain.RIVER);
				x += randomStep();
				y += randomStep(-dir,1-dir);
			}
		}
		// Traps
		nseeds=(int) (Math.random()*width*Math.sqrt(size));
		for (int i=0; i<nseeds;i++) {
			int x=(int)(Math.random()*size*width);
			int y=(int)(Math.random()*size);
			setT(x,y,Terrain.TRAP);
		}
		// Ocean
		nseeds=(int) (Math.random()*4);
		growth=1.0-(1.0/(size*size/4));
		for (int i=0; i<nseeds;i++) {
			int x=randomStep(0,1)*size*width;
			int y=randomStep(0,1)*size;
			while (Math.random()<growth) {
				setT(x,y,Terrain.OCEAN);
				if (Math.random()<0.5)
					x += randomStep();
				else
					y += randomStep();
			}
		}		
	}
	
	public void initThings() {
		for (int i=0;i<size*width;i++)
			for (int j=0;j<size;j++)
				setO(i,j,Thing.NOTHING);
		// Batteries, in small clusters
		int x,y;
		for (int i=0;i<width*Math.sqrt(size);i++) {
			do {
				x=(int) (Math.random()*size*width);
				y=(int) (Math.random()*size);
			} while (!isFreeSpot(x, y));
			do {
				setO(x,y,Thing.BATTERY);
				if (Math.random()<0.5)
					x += randomStep();
				else
					y += randomStep();
			}	while (Math.random()<0.75);
		}
		// Obstacles, in small clusters
		for (int i=0;i<Math.sqrt(size*width);i++) {
			do {
				x=(int) (Math.random()*size*width);
				y=(int) (Math.random()*size);
			} while (!isFreeSpot(x, y));
			do {
				setO(x,y,Thing.OBSTACLE);
				if (Math.random()<0.5)
					x += randomStep();
				else
					y += randomStep();
			}	while (Math.random()<0.66);
		}
		// Flags, each in 1/3 of the field
		do {
			x=(int) (Math.random()*(width*size/3.0));
			y=(int) (Math.random()*size);
		} while (!isFreeSpot(x, y));
		setO(x,y,Thing.FLAG1);
		do {
			x=(int) (width*size*2.0/3.0+Math.random()*(width*size/3.0));
			y=(int) (Math.random()*size);
		} while (!isFreeSpot(x, y));
		setO(x,y,Thing.FLAG2);
	}

	private void setO(int x, int y, Thing t) {
		if (between(0,x,size*width) && between(0,y,size))
			things[y][x]=t.symbol;
	}

	private int randomStep() {
		return (int)(Math.random()*3)-1;
	}
	private int randomStep(int a, int b) {
		return a+(int)(Math.random()*(b-a+1));
	}

	private void setT(int x, int y, Terrain t) {
		if (between(0,x,size*width) && between(0,y,size))
				terrain[y][x]=t.symbol;
	}
	private Terrain getT(int x, int y) {
		if (between(0,x,size*width) && between(0,y,size)) {
			char c=terrain[y][x];
			for (Terrain t: Terrain.values())
				if (t.symbol==c) return t;
		}
		return Terrain.VOID;
	}

	private Thing getO(int x, int y) {
		if (between(0,x,size*width) && between(0,y,size)) {
			char c=things[y][x];
			for (Thing t: Thing.values())
				if (t.symbol==c) return t;
		}
		return Thing.NOTHING;
	}

	public void moveO(int x, int y,char dir) {
		Direction d=Direction.forSymbol(dir);
		setO(x+d.dx,y+d.dy,getO(x,y));
		setO(x,y,Thing.NOTHING);
	}
	
	private char[][] getT() { // Warning: this exposes [row][column] rather than x,y
		return terrain;
	}
	private char[][] getO() { // Warning: this exposes [row][column] rather than x,y
		return things;
	}
	public char[][] getMap() {// Warning: this exposes [row][column] rather than x,y
		char [][] res=new char[size][size*width];
				for (int i=0;i<size;i++)
					for (int j=0;j<size*width;j++)
						res[i][j]=(things[i][j]==Thing.NOTHING.symbol?terrain[i][j]:things[i][j]);
		return res;
	}
	
	public boolean isFreeSpot(int x, int y) {
		if (getO(x,y)!=Thing.NOTHING)
			return false;
		if (getT(x,y)!=Terrain.GRASS)
			return false;
		int icntG=0,ocntG=0;
		for (int i=x-1;i<=x+1;i++)
			for (int j=y-1;j<=y+1;j++)
				if (getT(i,j)==Terrain.GRASS)
					icntG++;
		if (icntG<3)
			return false;

		for (int i=x-2;i<=x+2;i++)
			for (int j=y-2;j<=y+2;j++)
				if (getT(i,j)==Terrain.GRASS)
					ocntG++;
		return ocntG>18;
	}

	// returns what is on the map at (x,y)
	public char getMap(int x, int y) {
		Thing o=getO(x,y);
		if (o==Thing.NOTHING)
			return getT(x,y).symbol;
		else
			return getO(x,y).symbol;
	}

	// returns what is on the map 1 step in direction dir from (x,y)
	public char getMap(int x, int y, char dir) {
		Direction d=Direction.forSymbol(dir);
		return getMap(x+d.dx,y+d.dy);
	}

	
	private boolean between(int min, int x, int max) {
		return min<=x && x<max;
	}
	
	public static void main(String[] args) {
		GameMap gm=new GameMap(64,2);
		gm.initTerrain();
		gm.initThings();
		char[][] map=gm.getMap();
		for (int i=0;i<64;i++)
			System.out.println(map[i]);
	}

	public static boolean isTrap(char target) {
		return target==Terrain.TRAP.symbol;
	}

	public static boolean isRecharge(char target) {
		return target==Thing.BATTERY.symbol;
	}

	public void consumeO(int x, int y) {
		setO(x,y,Thing.NOTHING);
	}

	public static int team(char target) {
		if (target==Thing.FLAG1.symbol) return 0;
		if (target==Thing.FLAG2.symbol) return 1;
		throw new IllegalArgumentException("Team for non-flag");
		// TODO: we could also be more lenient...
	}

	public static boolean isWalkable(char target) {
		return target==Terrain.GRASS.symbol
				|| target==Terrain.RIVER.symbol
				|| target==Terrain.TRAP.symbol
				|| target==Thing.BATTERY.symbol
				|| target==Thing.NOTHING.symbol;	// TODO this last one may be unnecessary and dangerous
	}

	public static boolean isMoveable(char target) {
		return target==Thing.OBSTACLE.symbol;
	}

	public static boolean isFlag(char target) {
		return target==Thing.FLAG1.symbol || target==Thing.FLAG2.symbol;
	}

	public boolean canShootFrom(char tile) {
		return tile==Terrain.GRASS.symbol;
		// - cannot shoot from VOID, WALL, RIVER, OCEAN, TRAP Terrain
		//   a player should never be on VOID, WALL, OCEAN Terrain
		// - we ignore Things that may be on the spot
		//   a player should never be on an OBSTACLE or FLAGx Thing
	}
	public boolean canShootOver(char tile) {
		return tile!=Terrain.WALL.symbol
				&& tile!= Terrain.VOID.symbol
				&& tile!= Thing.OBSTACLE.symbol;
		// - cannot shoot over WALL or VOID or OBSTACLE
	}

}
