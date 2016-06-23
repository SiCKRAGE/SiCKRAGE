from hashlib import md5

########################################
## hashlib.md5
########################################

def test_md5():
    assert md5('').hexdigest() == 'd41d8cd98f00b204e9800998ecf8427e'
    assert md5('\n').hexdigest() == '68b329da9893e34099c7d8ad5cb9c940'
    assert md5('123').hexdigest() == '202cb962ac59075b964b07152d234b70'
    assert md5('123\n').hexdigest() == 'ba1f2511fc30423bdbb183fe33f3dd0f'
