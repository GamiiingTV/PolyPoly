fx_version 'cerulean'
game 'gta5'

name        'dynamic-economy'
author      'YourName'
version     '1.0.0'
description 'Dynamic supply & demand economy — real-time price fluctuation for FiveM'
url         'https://cfx.re/marketplace'

lua54 'yes'

shared_scripts {
    'config.lua',
}

server_scripts {
    '@oxmysql/lib/MySQL.lua',
    'server/debug.lua',   -- must load before server.lua
    'server/server.lua',
}

client_scripts {
    'client/client.lua',
}

ui_page 'ui/index.html'

files {
    'ui/index.html',
    'ui/style.css',
    'ui/app.js',
}

dependencies {
    'oxmysql',
}
