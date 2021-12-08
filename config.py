class Config:
  __conf = {
    "username": 'davidbacon@dabbleofdevops.com',
    "token" : '52iSDZYWNaXaeoXlbMmYph16rdwWD8/PvwGJvAAue+GqIkE0YgxFuZHQoHqYHzvskKkDlef/6SnOmtzaKn5oDA',
    "url" : 'https://dabbleofdevopshelp.zendesk.com',
    "zendesk_category_name" : 'General',
    "aws_s3_bucket" : 'zendesk.dabbleofdevops.com',
    "aws_access_key" : 'Your Access key here',
    "aws_secret" : 'Your secret here'
  }
  __setters = ["username", "token","aws_access_key","aws_secret"]

  @staticmethod
  def get(name):
    return Config.__conf[name]

  @staticmethod
  def set(name, value):
    if name in Config.__setters:
      Config.__conf[name] = value
    else:
      raise NameError("Name not accepted in set() method")
