from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Incluir todos los submódulos de blinker
hiddenimports = collect_submodules('blinker')

# Incluir todos los submódulos de selenium-wire y selenium
hiddenimports += collect_submodules('selenium')
hiddenimports += collect_submodules('seleniumwire')

# Incluir los archivos de datos necesarios de selenium-wire
datas = collect_data_files('seleniumwire')

# Agregar cualquier otro paquete necesario manualmente si no se detecta automáticamente
hiddenimports += [
    'selenium.webdriver.common', 
    'selenium.webdriver.remote',
    'selenium.webdriver.support',
    'selenium.webdriver.common.action_chains',
    'selenium.webdriver.common.by',
    'selenium.webdriver.common.keys',
    'selenium.webdriver.common.proxy',
    'selenium.webdriver.firefox',
    'selenium.webdriver.chrome',
    'selenium.webdriver.edge',
    'selenium.webdriver.ie',
    'selenium.webdriver.opera',
    'selenium.webdriver.safari',
    'selenium.webdriver.support.expected_conditions',
    'selenium.webdriver.support.wait',
    'selenium.webdriver.support.select',
    'seleniumwire.thirdparty.mitmproxy',
    'seleniumwire.thirdparty.mitmproxy.net',
    'seleniumwire.thirdparty.mitmproxy.options',
    'seleniumwire.thirdparty.mitmproxy.connections',
    'seleniumwire.thirdparty.mitmproxy.platform',
    'seleniumwire.thirdparty.mitmproxy.ctx',
]
