from PyInstaller.utils.hooks import collect_data_files
import pprint

datas = collect_data_files('llama_cpp')
pprint.pprint(datas)
