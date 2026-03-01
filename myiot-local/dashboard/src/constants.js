import { Thermometer, DoorOpen, ShieldAlert, Lightbulb, Zap, Cctv, Sofa, Bed, Utensils, Bath } from 'lucide-react';

// Room Configuration Mapping
export const ROOM_MAPPING = {
    'salon': 'Living Room',
    'entree': 'Kitchen',
    'cuisine': 'Kitchen',
    'bureau': 'Bedroom',
    'chambre': 'Bedroom',
    'bedroom': 'Bedroom',
    'chambre1': 'Bathroom',
    'bathroom': 'Bathroom',
};

// Sensor Type Configuration (Icons and Colors)
export const SENSOR_CONFIG = {
    'temperature': { name: 'Temperature Sensor', icon: Thermometer, color: '#e67e22' },
    'door': { name: 'Door Sensor', icon: DoorOpen, color: '#ff3f34' },
    'door_sabotage': { name: 'Sabotage Sensor', icon: ShieldAlert, color: '#4865ff' },
    'luminosity': { name: 'Light Sensor', icon: Lightbulb, color: '#f1c40f' },
    'battery_porte': { name: 'Door Battery', icon: Zap, color: '#2ecc71' },
    'motion': { name: 'Motion Sensor', icon: Cctv, color: '#4865ff' },
    'smoke': { name: 'Smoke Detector', icon: Zap, color: '#e67e22' }
};

// List of allowed sensor types to display
export const ALLOWED_TYPES = ['temperature', 'door', 'door_sabotage', 'luminosity', 'battery_porte'];

// Room UI Icons
export const ROOM_UI_CONFIG = [
    { name: 'Living Room', icon: Sofa },
    { name: 'Bedroom', icon: Bed },
    { name: 'Kitchen', icon: Utensils },
    { name: 'Bathroom', icon: Bath },
];
