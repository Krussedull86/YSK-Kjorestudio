import no.talappen.ysk.StopCounter;
public class StopCounterTest {
 public static void main(String[] args){
  if(StopCounter.next("")!=1||StopCounter.next("0.0")!=1||StopCounter.next("4")!=5||StopCounter.next("4,0")!=5)throw new AssertionError("manual and button counts");
  int count=0;for(int i=0;i<20;i++)count=StopCounter.next(String.valueOf(count));if(count!=20)throw new AssertionError("repeated taps");
  if(StopCounter.next("2")!=3)throw new AssertionError("manual correction");
  for(String s:new String[]{"-1","1.5","NaN","Infinity","2147483647","text"}){boolean rejected=false;try{StopCounter.next(s);}catch(IllegalArgumentException e){rejected=true;}if(!rejected)throw new AssertionError("invalid count: "+s);}
  System.out.println("Stop counter: repeated taps, manual correction, decimal integer input and invalid/overflow tests passed.");
 }
}
