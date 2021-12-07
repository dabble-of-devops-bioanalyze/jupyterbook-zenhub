class Config:
  __conf = {
    "username": "",
    "token" : "",
    "url" : 'https://dabbleofdevopshelp.zendesk.com',
    "zendesk_category_name" : "General",
    "aws_s3_bucket" : 'zendesk.dabbleofdevops.com',
    "aws_access_key" : "",
    "aws_secret" : ""
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
