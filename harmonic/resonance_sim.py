import math, random, time
output = 0.0; rate = 0.1
for t in range(1,31):
    raw = math.sin(t*0.4)*5 + random.uniform(-1,1)
    error = raw - output
    output += rate*error
    print(f"{t:02d}\t{raw:6.2f}\t{output:6.2f}")
    time.sleep(0.2)
