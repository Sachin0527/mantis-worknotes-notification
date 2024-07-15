from src import MantisWorkNotesNotification


def main():
    try:
        m_w_p = MantisWorkNotesNotification(time_window=100000)
        results = m_w_p.mantis_worknotes_notification()
        print(results)
    except Exception as ex:
        print(ex)


if __name__ == '__main__':
    main()
