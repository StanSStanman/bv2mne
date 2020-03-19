from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

def get_decimated(db_bv):
    zip_url = 'https://cloud.int.univ-amu.fr/index.php/s/4kGER6oest86oy3/download'
    print('Downloading decimation files...')
    with urlopen(zip_url) as zip_file:
        print('Unzipping decimation files...')
        with ZipFile(BytesIO(zip_file.read())) as zfile:
            zfile.extractall(db_bv)
    print('Decimation files saved in {0}'.format(db_bv))
    return

if __name__ == '__main__':
    get_decimated('D:\\Databases\\toy_db\\db_brainvisa')