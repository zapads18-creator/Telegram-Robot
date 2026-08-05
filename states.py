from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    choosing_region = State()
    choosing_district = State()
    choosing_dacha = State()
    entering_check_in = State()
    entering_check_out = State()
    entering_phone = State()
    confirming = State()


class OwnerContractStates(StatesGroup):
    entering_full_name = State()
    entering_phone = State()
    awaiting_agreement = State()


class AddDachaStates(StatesGroup):
    entering_name = State()
    entering_description = State()
    choosing_region = State()
    choosing_district = State()
    entering_address = State()
    entering_price = State()
    entering_contact_phone = State()
    entering_photo = State()
