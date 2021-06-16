package it.unipi.di.smartapp.amongais.logging;

import java.io.IOException;
import java.util.HashSet;
import java.util.Set;
import java.util.logging.FileHandler;
import java.util.logging.Handler;
import java.util.logging.Level;
import java.util.logging.LogRecord;
import java.util.logging.Logger;
import java.util.logging.SocketHandler;

public class LogUtil {

	private static Set<Logger> openLoggers=new HashSet<Logger>();
	
	public static Logger initLogger(String base,String name) {
		String logName=mkName(base,name);
		Logger log=Logger.getLogger(logName);
		openLoggers.add(log);
		try {
			FileHandler fh=new FileHandler("/home/gervasi/DIDATTICA/SmartApp2021/LOGS/tmp/"+logName+"-%u-%g.txt");
			fh.setFormatter(new LogFormatter());
			Handler[] hs = log.getHandlers();
			for (Handler h: hs)
				log.removeHandler(h);
			log.setUseParentHandlers(false);
			log.addHandler(fh);
			log.setLevel(Level.ALL);
		} catch (IOException e) {
			Logger.getGlobal().severe("Cannot open log file "+logName);
		}
		return log;
	}
	
	public static Logger getLogger(String base,String name) {
		Logger log=Logger.getLogger(mkName(base,name));
		return log;
	}
	
	public static void closeLogger(String base, String name) {
		String logName=mkName(base,name);
		Logger log=Logger.getLogger(logName);
		log.info("--- closed ---");				// TODO this seems to end up in the global logger. Investigate.
		for (Handler h: log.getHandlers()) {
			h.flush(); // feeling anxious
			h.close();
		}
		openLoggers.remove(log);
	}
	
	private static String mkName(String base,String name) {
		return base+"-"+name;
	}

	public static Set<Logger> getOpenLoggers() {
		return openLoggers;
	}
}
