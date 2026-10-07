package no.talappen.ysk;
import android.content.*;import android.security.keystore.*;import android.util.Base64;import java.security.*;import javax.crypto.*;import javax.crypto.spec.*;
public class Secure {
 static final String ALIAS="ysk_session_v1";
 static SecretKey key()throws Exception{KeyStore s=KeyStore.getInstance("AndroidKeyStore");s.load(null);if(!s.containsAlias(ALIAS)){KeyGenerator g=KeyGenerator.getInstance("AES","AndroidKeyStore");g.init(new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());g.generateKey();}return (SecretKey)s.getKey(ALIAS,null);}
 public static void put(Context c,String text)throws Exception{Cipher x=Cipher.getInstance("AES/GCM/NoPadding");x.init(Cipher.ENCRYPT_MODE,key());String value=Base64.encodeToString(x.getIV(),Base64.NO_WRAP)+":"+Base64.encodeToString(x.doFinal(text.getBytes("UTF-8")),Base64.NO_WRAP);if(!c.getSharedPreferences("secure",0).edit().putString("session",value).commit())throw new Exception("Kunne ikke lagre innlogging.");}
 public static String get(Context c)throws Exception{String value=c.getSharedPreferences("secure",0).getString("session","");if(value.isEmpty())return "";String[] parts=value.split(":");Cipher x=Cipher.getInstance("AES/GCM/NoPadding");x.init(Cipher.DECRYPT_MODE,key(),new GCMParameterSpec(128,Base64.decode(parts[0],Base64.NO_WRAP)));return new String(x.doFinal(Base64.decode(parts[1],Base64.NO_WRAP)),"UTF-8");}
}
