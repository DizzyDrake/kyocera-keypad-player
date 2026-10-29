package org.roarin.kyocerakeypad.core;

import java.io.IOException;
import java.util.function.Consumer;

/** Pure-Java isolated candidate mutation: never changes the original state before
 *  a durable writer reports success. Does not itself certify Android AtomicFile.
 */
public final class StateMutation {
    private StateMutation() {}
    public interface Writer { boolean save(byte[] bytes) throws IOException; }
    public static PlayerState prepareAndSave(PlayerState original,
            Consumer<PlayerState> edit,Writer writer) throws IOException {
        if(original==null || edit==null || writer==null)throw new IllegalArgumentException("Missing argument");
        PlayerState candidate=StateCodec.decode(StateCodec.encode(original));
        edit.accept(candidate);
        byte[] bytes=StateCodec.encode(candidate);
        return writer.save(bytes)?candidate:original;
    }
}
