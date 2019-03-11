# Meteostation
Meteostation (NodeMCU) &amp; Control Station (Raspberry Pi)

### Senzor osvětlení BH1750
**Čtení hodnoty v luxech a následný výpis do sériové linky**<br>
Po zapojení senzoru do I2C sběrnice a zjištění jeho adresy, je pomocí knihovny `BH1750.h` <br>
měřena hodnota osvětlení, která je následně zapisována na sériovou linku.<br>
<br>
### Senzor teploty a vlhkosti HTU21D
**Čtení teploty a vlhkosti a následný výpis do sériové linky**<br>
Po zapojení senzoru do I2C sběrnice a zjištění jeho adresy je pomocí knihovny `SparkFunHTU21D.h`,<br>
měřena hodnota teploty a vlhkosti. Tyto veličiny jsou následně vypisovány na sériovou linku.<br>
<br>

## Napájecí obvod pro ESP
**Obvod napájí ESP z baterie**<br>
Baterie je připojena ke step-upu. Ten z proměnného napětí baterie vytvoří stabilních 5 Voltů, které jsou poté vedeny přes USB do ESP.

## Napájení baterie ze solárního panelu
**Tento obvod napájí jak baterii solárním panelem, tak ESP z baterie.**<br>
Zde je využit také modul pro napájení baterie, ke kterému je připojen solární panel na vstup a baterie na výstup. Nabíjení baterie se indikuje LEDkou na modulu. Je-li baterie plně nabitá, svítí také druhá LEDka. Jako v úkolu 15a je baterie připojena na step-up. Ten zvýší napětí na 5 Voltů, kterými se napájí ESP.

## Měření napětí baterie a indikování stavů
**ESP měří napětí baterie, kterou přepočítá a následně posílá na lokální MQTT server, běžící na Raspberry. Na Raspberry se data zpracovávají a za pomoci LEDky se indikuje vybití baterie.**<br>
Pro měření stavu kapacity baterie je baterie připojena na analogový pin ESP. ESP z tohoto pinu měří hodnotu, která je za pomoci napěťového děliče (zabudovaného rezistoru + 100k rezistor) přepočítána na napětí, když víme že 4.2V = 1023 (podle našeho napěťového děliče)<br>
Takže jednoduše stačí namapovat hodnotu z analogu do napětí (4.2V = 1023, 0V = 0) a zároveň můžeme i mapovat měřenou hodnotu na kapacitu baterie.<br>
<br>
V meteostanici je integrovaná LEDioda, která nám blikáním indikuje, jak je baterie vybitá.<br>
Pokud baterie má více než 30% kapacity, LEDioda je vyplá.<br>
Pokud ale kapacita klesne pod 30%, LEDioda začně blikat a čím víc je vybitá, tím rychleji bliká.<br>
<br>
Kapacita a napětí baterie se posílají přes lokální MQTT server na Raspberry (ridiciCentralu).<br>
Řídicí Centrála při aktualizaci odebíraného topicu ve funkci `on_local_message` zjistí, zda má baterie pod 30% kapacity,<br>
a pokud ano, tak rozsvítí LEDiodu i na Řídicí centrále.<br>
<br>

### Připojení ESP do lokální sítě pomocí WiFi
**ESP se připojí na existující síť**<br>
Meteostanice se při zapnutí snaží připojit k WiFi síti, kterou má nastavenou jako konstantu v hlavičce `main.cpp`.<br>
O korektní připojení do sítě Wifi se stará funkce `setup_wifi`, jež využívá možností knihovny `ESP8266Wifi`.<br>
Jejím úkolem je připojit desku do sítě, a nebo počkat do doby, kdy síť již dostupná bude.<br>
<br>
### Odesílání dat na Raspberry
**Meteostanice odesíla data pomocí MQTT protokolu na lokalní MQTT broker na Raspberry.**<br>
Meteostanice se po úspěšném připojení do sítě WiFi pokusí připojit na lokální MQTT broker,<br>
který běží na Raspberry (Mosquitto broker).<br>
<br>
K tomuto připojení slouží funkce `reconnect`, která se pokusí připojit k MQTT brokeru.<br>
Dojde-li k úspěšnému připojení, funkce vygeneruje náhodné ID pod kterým se meteostanice bude nadále identifikovat.<br>
Při neúspěšném připojení funkce *počká* na nalezení MQTT brokeru.<br>
Pokud meteostanice ztratí spojení s MQTT brokerem, aktivuje se opět tato funkce a celý proces proběhne znovu.<br>
<br>
Posílání dat se provádí přímo v hlavní smyčce `loop`, kde se po testu spojení s MQTT brokerem<br>
změří hodnoty na senzorech a následně se pošlou na MQTT broker pod topic `meteo1/<veličina>`.<br>
Například měrení světla je posláno pod topic `meteo1/light`. *(meteo1/temp; meteo1/humd) pro ostatní*<br>
<br>
Momentálně není odebírání zpráv z MQTT brokeru nijak využíváno, ale je plně implementováno.<br>
A to ve funkci `callback`, která se zavolá pokaždé když se aktualizuje odebíraný topic.<br>
<br>
### Zobrazení dat na displeji Raspberry
**RidiciCentrala odebírá topicy meteostanice a následně přečtené hodnoty vypisuje na displej.**<br>
Podobně jako u meteostanice jsou zde přítomny dvě nové funkce:<br>
1. Funkce `on_local_connect`, která pouze vypíše kontrolní hlášku a znovu začne odebírat topicy meteostanice `meteo1/#`.<br>
<br>
2. Funkce `on_local_message`, která *chytá* změny v odebíraných topicích. <br>
Ta zjistí o jakou veličinu se jedná a následně jí uloží do paměti.<br>
<br>
Nad hlavní smyčkou s cyklem `while` se také inicializuje spojení s MQTT serverem.<br>
Raspberry se připojí na `localhost` (sám na sebe) a zapne poslech asynchronně, aby se funkce MQTT protokolu nepřela s ostatními funkcemi.<br>
<br>
Nasledně se přijaté veličiny vypíšou pomocí již existujících funkcí.<br>
<br>

## 3D Modely
**Návrh krabičky pro ochranu obvodu**<br>
Díky studentské licenci Autodesk Inventoru jsme byli schopni celé řešení namodelovat a sestavit předem. Tímto jsme si ověřili, že vše sedí jak má a nebude nutné žádné části tisknout vícekrát kvůli chyb v měření.<br>
<br>
**Stažené modely**<br>
Pro konečnou sestavu v AD Inventoru jsme použili několik komunitních 3D modelů - obvodů, arduina a dalších.<br>
Tyto modely byly použity pro kontrolu, jestli vše bude sedět, jak má.<br>
<br>
**Krabička pro ESP (Snímky/Fotky ESPBox)**<br>
V hlavní části meteostanice se nachází *NodeMCU*, nabíjecí obvod s baterií a senzory pro měření.<br>
*NodeMCU* má speciálně navržený vertikální držák, který zajištujě solidní uchopení a dobrý přístup k I/O pinům.<br>
Hned vedle *NodeMCU* se nachází stojan na I<sup>2</sup>C sběrnici, ke které jsou připojeny meřící senzory.<br>
Senzory mají speciální dutinu, do které jsou zasunuty. Tato dutina dovoluje senzorům měřit všechny veličiny a zároveň být v bezpečí krabičky.<br>
Izolovana díra se senzory je poté ze shora zakryta průhledným materiálem, aby senzor světla stále fungoval, ale z druhé strany zůstává otevřená.<br> 
Tímto způsobem se minimalizuje jakékoliv riziko kontaktu s vodou a maximalizuje se přesnost měření.<br>
<br>
**Napájecí obvod**<br>
Druhá polovina krabičky je přizpůsobena pro nabíjecí obvod.<br>
Uprostřed krabice se nachází dlouhá vyvýšená plocha pro umístění napájecího obvodu, <br>
který musel být mírně modifikován, aby se do krabice vlezl (místo použití USB pro napájení ESP atd.. přímo napájené drátky). <br>
Baterie je přes vyrobenou nadstavbu, která je k nabíjecímu obvodu připojena ze shora, připojena a nabíjena.<br>
Pro nabíjecí konektor microUSB byla po vytisknutí vyvrtaná díra.<br>
<br>
**Arduino a trasování slunce**<br>
Pro arduino a kabeláž tvořící heliotracker je nad hlavní krabicí menší krabička, na které sedí samotný mechanismus pro sledování slunce.<br>
Všechny tyto díly jsou navzájem sešroubovány a kabeláž mezi nimi je řešena kruhovými dírami uprostřed každé části.<br>
<br>
