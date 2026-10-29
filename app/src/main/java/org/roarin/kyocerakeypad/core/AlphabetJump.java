package org.roarin.kyocerakeypad.core;

import java.text.Normalizer;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/** Pure title index for physical-keypad library browsing; never edits saved state. */
public final class AlphabetJump {
    private AlphabetJump() {}

    /** A-Z for the first significant title letter (accent folded); # otherwise. */
    public static char bucket(String title) {
        if (title == null || title.trim().isEmpty()) return '#';
        String normalized = Normalizer.normalize(title.trim(), Normalizer.Form.NFD)
            .replaceAll("\\p{M}+", "").toUpperCase(Locale.ROOT);
        if (normalized.isEmpty()) return '#';
        char first = normalized.charAt(0);
        return first >= 'A' && first <= 'Z' ? first : '#';
    }

    /** Only show buckets actually present, in A-Z order followed by non-A-Z. */
    public static Map<Character,Integer> counts(List<String> titles) {
        Map<Character,Integer> all = new LinkedHashMap<>();
        for (char c='A'; c<='Z'; c++) all.put(c, 0);
        all.put('#', 0);
        for (String title : titles) {
            char c=bucket(title);
            all.put(c, all.get(c)+1);
        }
        all.entrySet().removeIf(e -> e.getValue()==0);
        return all;
    }

    /** Zero-based index in the displayed (already sorted and filtered) title list. */
    public static int firstMatchingIndex(List<String> titles, char bucket) {
        for (int i=0; i<titles.size(); i++) {
            if (bucket(titles.get(i)) == bucket) return i;
        }
        return -1;
    }
}
