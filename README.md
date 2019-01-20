# elva

Online playable game based on the Persian card game https://en.wikipedia.org/wiki/Pasur_(card_game)

Soon with AI player.


# Start production system
`ELVA_SECRET_KEY=`cat SECRET_KEY` docker-compose -f docker-compose.yml up --build -d`


# KNOWN PROBLEMS IN WINDOWS

Fails to install twisted? USE: https://www.lfd.uci.edu/~gohlke/pythonlibs/#twisted

Fails to install channels_redis? Install VS build tools https://wiki.python.org/moin/WindowsCompiler
