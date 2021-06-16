package it.unipi.di.smartapp.amongais.logging;

import java.util.logging.Formatter;
import java.util.logging.LogRecord;

public class LogFormatter extends Formatter {

	public LogFormatter() {
		super();
	}

	@Override
	public String format(LogRecord record) {
		return String.format("%d %s %s\n", record.getSequenceNumber(),record.getMillis(),record.getMessage());
	}

}
