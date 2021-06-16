package it.unipi.di.smartapp.amongais.gameserver;

public enum PlayerState {
	CREATED,LOBBYOWNER,LOBBYGUEST,ACTIVE,KILLED,LEFT;

	boolean inLobby() {
		return this==LOBBYOWNER || this==LOBBYGUEST;
	}
	boolean canJoin() {
		return this==CREATED || this==LOBBYOWNER;
	}
}
