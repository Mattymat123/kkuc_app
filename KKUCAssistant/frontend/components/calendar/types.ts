export interface TimeSlot {
  day: string;
  date: string;
  time: string;
  datetime?: string;
}

export interface CalendarSlotsData {
  slots: TimeSlot[];
}

export interface BookingDetails {
  name: string;
  substanceType: string;
  kommune: string;
  ageGroup: string;
  notes: string;
}

export interface BookingDetailsData {
  selectedSlot: TimeSlot;
}

export interface BookingConfirmationData {
  bookingData: {
    name: string;
    selectedSlot: TimeSlot;
    substanceType: string;
    kommune: string;
    ageGroup: string;
    notes: string;
  };
}
