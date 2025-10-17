export interface TimeSlot {
  day: string;
  date: string;
  time: string;
  datetime?: string;
}

export interface CalendarSlotsData {
  slots: TimeSlot[];
}
