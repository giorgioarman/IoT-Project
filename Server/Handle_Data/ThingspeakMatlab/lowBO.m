% Channel ID to read data from 
readChannelID = 779308; 
   
% Channel Read API Key   
readAPIKey = 'D86SV78XNDD5SKE0'; 

[BO,time] = thingSpeakRead(readChannelID,'Fields',1,'DateRange',[datetime('now')-30, datetime('now')],'ReadKey',readAPIKey); % per visualizzare l'ultima settimana datetime('now') - 7, datetime('now')

flag = 0;
j = 1;
k = 1;
%number of critical events:
for i = 1:length(BO)
    if BO(i) < 80 && flag == 0
        crit(j) = datenum(time(i));
        flag = 1;
        j = j + 1;
    end
    if flag == 1 && BO(i) > 85
        ris(j - 1) = datenum(time(i));
        flag = 0;
    end
    if i == length(BO) && flag == 1
        crit(length(crit)) = [];
    end
end

for i1 = 1:length(crit)
    tempo(i1) = etime(datevec(ris(i1)),datevec(crit(i1)));
end

bar(tempo); 
xlabel('# of Critical events'); 
ylabel('Number of seconds until resolution'); 
title('Time of resolution of critical events \newline for low blood oxygen in the last 30 days');
