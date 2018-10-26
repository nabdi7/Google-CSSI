location = "the place"
user = "Zach"
emailTo = "zpghera00@gmail.com"
emailBody =
emailHtml =

message = mail.EmailMessage(
        sender="college.connect.cssi@gmail.com",
        subject="Your account has been approved")

message.to = "Albert Johnson <Albert.Johnson@example.com>"
message.body = """Dear Albert:

Your example.com account has been approved.  You can now visit
http://www.example.com/ and sign in using your Google Account to
access new features.

Please let us know if you have any questions.

The example.com Team
"""

    message.send()
