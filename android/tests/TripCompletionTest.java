import no.talappen.ysk.TripCompletion;
import java.util.*;
public class TripCompletionTest {
 public static void main(String[] args){Map<String,String> fields=new HashMap<>();if(!TripCompletion.missing(fields).contains("sjåfør"))throw new AssertionError("Empty draft must be incomplete");for(String k:TripCompletion.KEYS)fields.put(k,"-");if(!TripCompletion.missing(fields).isEmpty())throw new AssertionError("Explicit omissions must be complete");fields.put("minutes","  ");fields.put("komfort","");String missing=TripCompletion.missing(fields);if(!missing.equals("forbrukt tid, komfort"))throw new AssertionError(missing);fields.put("minutes","12.5");fields.put("komfort","Bra");if(!TripCompletion.missing(fields).isEmpty())throw new AssertionError("Finishing same draft must clear warning");System.out.println("Trip completion tests passed");}
}
