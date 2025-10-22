import gzip


def compress(s: str) -> bytes:
    return gzip.compress(s.encode('utf-8'))


def decompress(data: bytes) -> str:
    return gzip.decompress(data).decode('utf-8')


if __name__ == '__main__':
    st = """
A maioria dos animais consumidos aqui no Brasil, como vacas, galinhas e porcos, são herbívoros ou onívoros. Embora alguns, como jacaré, sejam consumidos em algumas regiões, a carne de animais carnívoros não é comum devido a vários fatores:

Existe risco de contaminação, já que esses animais acumulam microrganismos e parasitas dos outros animais que consomem, tornando-os mais suscetíveis a transmitir doenças;

A carne de predadores tende a ser mais magra, dura e menos saborosa;… - Veja mais em https://www.uol.com.br/vivabem/noticias/redacao/2025/03/05/nao-e-costume-no-brasil-por-que-nao-comemos-carne-de-bichos-carnivoros.htm?cmpid=copiaecola
    """
    c = compress(st)
    d = decompress(c)
    print('Original', len(st), st)
    print('Compressed', len(c), c)
    print('Decompressed', len(d), d)
