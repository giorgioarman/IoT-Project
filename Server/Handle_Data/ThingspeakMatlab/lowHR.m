% Channel ID to read data from 
readChannelID = 779308; 
   
% Channel Read API Key   
readAPIKey = 'D86SV78XNDD5SKE0'; 

[iHR,time] = thingSpeakRead(readChannelID,'Fields',2,'DateRange',[datetime('now')-30, datetime('now')],'ReadKey',readAPIKey); 

flag = 0;
%keyboard;
j = 1;
k = 1;
%number of critical events:
for i = 1:length(iHR)
    if iHR(i) < 54 && flag == 0
        crit(j) = datenum(time(i));
        flag = 1;
        j = j + 1;
    end
    if flag == 1 && iHR(i) > 60
        ris(j - 1) = datenum(time(i));
        flag = 0;
    end
    if i == length(iHR) && flag == 1
        crit(length(crit)) = [];
    end
end

for i1 = 1:length(crit)
    tempo(i1) = etime(datevec(ris(i1)),datevec(crit(i1)));
end

bar(tempo); 
xlabel('# of Critical events'); 
ylabel('Number of seconds until resolution'); 
title('Time of resolution of critical events \newline for low heart rate in the last 30 days');
