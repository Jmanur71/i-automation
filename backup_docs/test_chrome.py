from llm_client import ChromeClient

if __name__ == '__main__':
    try:
        client = ChromeClient(headless=False)
        def cb(chunk):
            print('CHUNK:', chunk)
        res = client.query('what is the capital of France?', cb)
        print('RESULT:', res)
    except Exception as e:
        print('ERROR:', e)
    finally:
        try:
            client.close()
        except Exception:
            pass
