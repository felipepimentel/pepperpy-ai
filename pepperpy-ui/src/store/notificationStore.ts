import { create } from 'zustand';
import { NotificationType } from '../components/Notification';

interface NotificationState {
  message: string;
  type: NotificationType;
  show: boolean;
  showNotification: (message: string, type: NotificationType) => void;
  hideNotification: () => void;
}

const useNotificationStore = create<NotificationState>((set) => ({
  message: '',
  type: 'info',
  show: false,
  
  showNotification: (message: string, type: NotificationType) => {
    set({ message, type, show: true });
  },
  
  hideNotification: () => {
    set({ show: false });
  }
}));

export default useNotificationStore; 