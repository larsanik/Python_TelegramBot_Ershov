import datetime


class Calendar:
    def __init__(self):
        self.events = {}

    # метод create_event
    def create_event(self, event_name, event_date, event_time, event_details) -> int:
        event_id = len(self.events) + 1
        event = {
            "id": event_id,
            "name": event_name,
            "date": event_date,
            "time": event_time,
            "details": event_details
        }
        self.events[event_id] = event
        return event_id

    # метод read_event
    def read_event(self, id_event) -> str:
        str_out = ''
        for key, val in self.events[id_event].items():
            str_out = str_out + str(key) + ': ' + str(val) + ' | '
        return str_out

    # метод edit_event
    def edit_event(self, id_event, new_event_details) -> None:
        self.events[id_event]['details'] = new_event_details

    # метод delete_event
    def delete_event(self, id_event) -> None:
        del self.events[id_event]

    # метод display_event
    def display_event(self) -> str:
        str_out = ''
        for el in self.events.items():
            # print(el[1].items())
            for key, val in el[1].items():
                str_out = str_out + str(key) + ': ' + str(val) + ' | '
            str_out = str_out + '\n'
        return str_out


calendar = Calendar()
for i in range(5):
    event_name = f'event {i}'
    event_date = datetime.datetime.now().strftime('%Y-%m-%d')
    event_time = datetime.datetime.now().time().strftime('%H:%M')
    event_details = f'Какое то событие {i}'
    # Создать событие с помощью метода create_event класса Calendar
    event_id = calendar.create_event(event_name, event_date, event_time, event_details)

# print(calendar.read_event(1))
# print(calendar.edit_event(1, 'Новое описание события'))
# print(calendar.read_event(1))
# print(calendar.events)

# for i in calendar.events.items():
#     print(i)
# print('************************************************************************')
calendar.delete_event(3)
calendar.delete_event(5)
#
# for i in calendar.events.items():
#     print(i)
print(calendar.display_event())