import no.talappen.ysk.TripTimes;
public class TripTimesTest {
 public static void main(String[] args){if(!TripTimes.clock("815").equals("08:15")||!TripTimes.clock("8.15").equals("08:15"))throw new AssertionError("Clock normalization");if(TripTimes.minutes("08:15","09:40")!=85||TripTimes.minutes("23:45","00:15")!=30)throw new AssertionError("Minute duration");if(TripTimes.minutes("08:15","")!=null)throw new AssertionError("Incomplete times");for(String bad:new String[]{"25:00","12:60","xx","1:2"}){try{TripTimes.clock(bad);throw new AssertionError("Accepted invalid time");}catch(IllegalArgumentException expected){}}try{TripTimes.minutes("08:15","08:15");throw new AssertionError("Equal times");}catch(IllegalArgumentException expected){}System.out.println("Trip time tests passed");}
}
