from devtools import sformat, sprint

sprint('this is red', sprint.red)

sprint('this is bold underlined blue on a green background. yuck',
       sprint.blue, sprint.bg_yellow, sprint.bold, sprint.underline)

v = sformat('i am dim', sprint.dim)
print(repr(v))
# > '\x1b[2mi am dim\x1b[0m'
