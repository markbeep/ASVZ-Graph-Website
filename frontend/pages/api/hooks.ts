import { CalendarDatum } from '@nivo/calendar'
import axios from "axios"
import { Serie } from '@nivo/line';
import { HistoryData, HistoryOrder, StringDatum, StringExtraProps, WeeklyDetails, WeeklyDetailsObject } from "./interfaces";
import { useQuery } from 'react-query';
import { HeatMapSerie } from '@nivo/heatmap';
import { showNotification } from '@mantine/notifications';

async function loadCountDay() {
  const response = await axios.get('/api/countday')
  return response.data as CalendarDatum[];
}

export function useCountDay() {
  const { isError, isLoading, data } = useQuery(["countday"], () =>
    loadCountDay(),
    {
      onError: (e: TypeError) => showNotification({
        title: "Error",
        message: `${e.message}`,
        color: "red",
      })
    }
  )
  return { isError, isLoading, data } as const
}


async function loadCountDaySport() {
  const url = "/api/countdaybar"
  const response = await axios.get(url)
  return response.data as Serie[];
}

export function useCountDaySport() {
  const { isError, isLoading, data } = useQuery(["countdaysport"], () =>
    loadCountDaySport(),
  )
  return { isError, isLoading, data } as const
}

async function loadSports() {
  const url = "/api/sports"
  const response = await axios.get(url)
  return response.data as string[];
}

export function useSports() {
  const { isError, isLoading, data } = useQuery(["sports"], () =>
    loadSports(),
  )
  return { isError, isLoading, data } as const
}

async function loadLocations() {
  const url = "/api/locations"
  const response = await axios.get(url)
  return response.data as string[];
}

export function useLocations() {
  const { isError, isLoading, data } = useQuery(["locations"], () =>
    loadLocations(),
  )
  return { isError, isLoading, data } as const
}

async function loadHistory(activities: string[], locations: string[], from: Date, to: Date, orderBy: HistoryOrder, desc: boolean) {
  if (activities.length === 0 || from === undefined || to === undefined) return [];
  let orderByKey = "date";
  switch (orderBy) {
    case HistoryOrder.activity:
      orderByKey = "sport";
      break;
    case HistoryOrder.location:
      orderByKey = "location";
      break;
    case HistoryOrder.spots_total:
      orderByKey = "places_max";
      break;
    case HistoryOrder.spots_free:
      orderByKey = "places_max-places_taken";
      break;
  }
  const body = JSON.stringify({ activities, locations, from: from.toISOString(), to: to.toISOString(), orderBy: orderByKey, desc });

  const url = "/api/history"
  console.log(`POST: ${url} | BODY ${body}`)
  const response = await axios.post(url, body)
  return response.data as HistoryData[];
}

export function useHistory(activities: string[], locations: string[], from: Date, to: Date, orderBy: HistoryOrder, desc: boolean) {
  const { isError, isLoading, data } = useQuery(["history", activities, locations, from, to, orderBy, desc], () =>
    loadHistory(activities, locations, from, to, orderBy, desc)
  );
  return { isError, isLoading, data } as const
}


async function loadHistoryLine(activities: string[], locations: string[], from: Date, to: Date) {
  if (activities.length === 0 || from === undefined || to === undefined) return [];
  const body = JSON.stringify({ activities, locations, from: from.toISOString(), to: to.toISOString() });

  const url = "/api/historyline"
  console.log(`POST: ${url} | BODY ${body}`)
  const response = await axios.post(url, body)
  return response.data as Serie[];
}

export function useHistoryLine(activities: string[], locations: string[], from: Date, to: Date) {
  const { isError, isLoading, data } = useQuery(["historyline", activities, locations, from, to], () =>
    loadHistoryLine(activities, locations, from, to)
  );
  return { isError, isLoading, data } as const
}

async function loadWeekly(activities: string[], locations: string[], from: Date, to: Date) {
  if (activities.length === 0 || from === undefined || to === undefined) return [];
  const body = JSON.stringify({ activities, locations, from: from.toISOString(), to: to.toISOString() });

  const url = "/api/weekly"
  const response = await axios.post(url, body)

  return response.data as HeatMapSerie<StringDatum, StringExtraProps>[];
}

export function useWeekly(activities: string[], locations: string[], from: Date, to: Date) {
  const { isError, isLoading, data } = useQuery(["weekly", activities, locations, from, to], () =>
    loadWeekly(activities, locations, from, to)
  );
  return { isError, isLoading, data } as const
}
