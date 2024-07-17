from src import MantisWorkNotesNotification


# Main method to trigger the process.
# Time_window is the time in minutes window for issues/notes extraction
def main():
    try:
        mantis_notification  = MantisWorkNotesNotification(time_window=1)
        results = mantis_notification.mantis_worknotes_notification()
        print(results)
    except Exception as ex:
        print(ex)


if __name__ == '__main__':
    main()
