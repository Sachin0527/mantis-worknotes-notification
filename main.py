from src import MantisWorkNotesNotification


# Main method to trigger the process.
# Time_window is the time in minutes window for issues/notes extraction
def main():
    try:
        mantis_notification  = MantisWorkNotesNotification(time_window=5)
        results = mantis_notification.mantis_worknotes_notification()
        print(results)

        #send the queued messages to email
        mantis_notification.send_all_messages_in_queue()
        print(results)
    except Exception as ex:
        print(ex)


if __name__ == '__main__':
    main()
