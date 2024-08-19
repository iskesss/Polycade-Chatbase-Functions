from PCH import PolycadeChatbaseHelper


print("> Hi! I'm the Polycade Chatbase Helper.")
pch = PolycadeChatbaseHelper()

# the PCH shell
while True:
    print(
        "-----------------------------------------------------------------------------"
    )
    user_response = input(
        """> Which function would you like me to run for you? Enter its number below
                1 : Update Google Sheets with all Q&As in the Polycade Helpcenter
                2 : Download all Q&As from Google Sheets
> """
    )
    if user_response == "1":
        pch.update_sheets_with_qnas()
    elif user_response == "2":
        pch.download_qnas_from_sheets()
    else:
        print(
            "> ERROR: Please enter a number corresponding to one of the available functions"
        )
