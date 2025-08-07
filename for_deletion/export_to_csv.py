
import json
import csv

# The JSON data from the previous API call
json_data = """
{
  "answer": "...",
  "tool_results": {
    "date_validation": {
      "current_time_local": "2025-08-07T12:00:00-04:00",
      "is_valid": true,
      "latest_available_date": "2025-08-07",
      "original_end_time": "2025-08-06T23:59:59-04:00",
      "original_start_time": "2025-07-31T00:00:00-04:00",
      "recommendations": [],
      "warnings": []
    },
    "installation_id": "4995d395-9b4b-4234-a8aa-9938ef5620c6",
    "installation_summary": {
      "data_coverage_percentage": 73.18181655687327,
      "downtime_minutes": 0.002033333333333333,
      "downtime_percentage": 1.441961956579621e-05,
      "elevators_with_data": 2,
      "elevators_without_data": 0,
      "expected_total_minutes": 10080.0,
      "total_elevators": 2,
      "total_minutes": 14099.2517,
      "uptime_minutes": 14099.249666666665,
      "uptime_percentage": 99.99998558038043
    },
    "machine_metrics": [
      {
        "daily_availability": [
          {
            "actual_hours": 11.999722222222221,
            "availability_percentage": 50.00000000000001,
            "date": "2025-07-31",
            "expected_hours": 23.99972222222222,
            "has_data": true
          },
          {
            "actual_hours": 23.99972222222222,
            "availability_percentage": 100.0,
            "date": "2025-08-01",
            "expected_hours": 23.99972222222222,
            "has_data": true
          },
          {
            "actual_hours": 23.99972222222222,
            "availability_percentage": 100.0,
            "date": "2025-08-02",
            "expected_hours": 23.99972222222222,
            "has_data": true
          },
          {
            "actual_hours": 23.99972222222222,
            "availability_percentage": 100.0,
            "date": "2025-08-03",
            "expected_hours": 23.99972222222222,
            "has_data": true
          },
          {
            "actual_hours": 23.99972222222222,
            "availability_percentage": 100.0,
            "date": "2025-08-04",
            "expected_hours": 23.99972222222222,
            "has_data": true
          },
          {
            "actual_hours": 23.999722222222225,
            "availability_percentage": 100.00000000000003,
            "date": "2025-08-05",
            "expected_hours": 23.99972222222222,
            "has_data": true
          },
          {
            "actual_hours": 23.999722222222218,
            "availability_percentage": 99.99999999999999,
            "date": "2025-08-06",
            "expected_hours": 23.99972222222222,
            "has_data": true
          }
        ],
        "data_coverage_percentage": 85.3411030066133,
        "downtime_minutes": 0.0013333333333333333,
        "downtime_percentage": 1.730587907907578e-05,
        "has_data": true,
        "intervals": [
          {
            "duration_minutes": 719.9934166666666,
            "end": "2025-07-31T12:00:00-04:00",
            "mode": "NOR",
            "start": "2025-07-31T00:00:00.395000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0098,
            "end": "2025-08-01T08:26:00.672000-04:00",
            "mode": "DCP",
            "start": "2025-08-01T08:26:00.084000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 55.03153333333333,
            "end": "2025-08-01T09:21:02.564000-04:00",
            "mode": "NOR",
            "start": "2025-08-01T08:26:00.672000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.010216666666666667,
            "end": "2025-08-01T09:21:03.177000-04:00",
            "mode": "DCP",
            "start": "2025-08-01T09:21:02.564000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 27.246416666666667,
            "end": "2025-08-01T09:48:17.962000-04:00",
            "mode": "NOR",
            "start": "2025-08-01T09:21:03.177000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0101,
            "end": "2025-08-01T09:48:18.568000-04:00",
            "mode": "DCP",
            "start": "2025-08-01T09:48:17.962000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 105.74805,
            "end": "2025-08-01T11:33:03.451000-04:00",
            "mode": "NOR",
            "start": "2025-08-01T09:48:18.568000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0102,
            "end": "2025-08-01T11:33:04.063000-04:00",
            "mode": "DCP",
            "start": "2025-08-01T11:33:03.451000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 57.06223333333333,
            "end": "2025-08-01T12:30:07.797000-04:00",
            "mode": "NOR",
            "start": "2025-08-01T11:33:04.063000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.010066666666666666,
            "end": "2025-08-01T12:30:08.401000-04:00",
            "mode": "DCP",
            "start": "2025-08-01T12:30:07.797000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 149.07153333333334,
            "end": "2025-08-01T14:59:12.693000-04:00",
            "mode": "NOR",
            "start": "2025-08-01T12:30:08.401000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0098,
            "end": "2025-08-01T14:59:13.281000-04:00",
            "mode": "DCP",
            "start": "2025-08-01T14:59:12.693000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 105.77203333333333,
            "end": "2025-08-01T16:44:59.603000-04:00",
            "mode": "NOR",
            "start": "2025-08-01T14:59:13.281000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.010216666666666667,
            "end": "2025-08-01T16:45:00.216000-04:00",
            "mode": "DCP",
            "start": "2025-08-01T16:44:59.603000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 27.6039,
            "end": "2025-08-01T17:12:36.450000-04:00",
            "mode": "NOR",
            "start": "2025-08-01T16:45:00.216000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0101,
            "end": "2025-08-01T17:12:37.056000-04:00",
            "mode": "DCP",
            "start": "2025-08-01T17:12:36.450000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 154.55171666666668,
            "end": "2025-08-01T19:47:10.159000-04:00",
            "mode": "NOR",
            "start": "2025-08-01T17:12:37.056000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009766666666666667,
            "end": "2025-08-01T19:47:10.745000-04:00",
            "mode": "DCP",
            "start": "2025-08-01T19:47:10.159000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 105.77258333333333,
            "end": "2025-08-01T21:32:57.100000-04:00",
            "mode": "NOR",
            "start": "2025-08-01T19:47:10.745000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.010133333333333333,
            "end": "2025-08-01T21:32:57.708000-04:00",
            "mode": "DCP",
            "start": "2025-08-01T21:32:57.100000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 55.053816666666665,
            "end": "2025-08-01T22:28:00.937000-04:00",
            "mode": "NOR",
            "start": "2025-08-01T21:32:57.708000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0098,
            "end": "2025-08-01T22:28:01.525000-04:00",
            "mode": "DCP",
            "start": "2025-08-01T22:28:00.937000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 139.73415,
            "end": "2025-08-02T00:47:45.574000-04:00",
            "mode": "NOR",
            "start": "2025-08-01T22:28:01.525000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.010066666666666666,
            "end": "2025-08-02T00:47:46.178000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T00:47:45.574000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 27.240366666666666,
            "end": "2025-08-02T01:15:00.600000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T00:47:46.178000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0101,
            "end": "2025-08-02T01:15:01.206000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T01:15:00.600000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 139.7402,
            "end": "2025-08-02T03:34:45.618000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T01:15:01.206000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009766666666666667,
            "end": "2025-08-02T03:34:46.204000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T03:34:45.618000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 82.23846666666667,
            "end": "2025-08-02T04:57:00.512000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T03:34:46.204000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.01015,
            "end": "2025-08-02T04:57:01.121000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T04:57:00.512000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 55.03965,
            "end": "2025-08-02T05:52:03.490000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T05:57:01.121000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0098,
            "end": "2025-08-02T05:52:04.078000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T05:52:03.490000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 154.56066666666666,
            "end": "2025-08-02T08:26:37.718000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T05:52:04.078000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009766666666666667,
            "end": "2025-08-02T08:26:38.304000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T08:26:37.718000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 32.74415,
            "end": "2025-08-02T08:59:30.539000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T08:26:38.304000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 73.34864999999999,
            "end": "2025-08-02T10:12:51.458000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T08:59:30.539000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.010083333333333333,
            "end": "2025-08-02T10:12:52.063000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T10:12:51.458000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 23.331316666666666,
            "end": "2025-08-02T10:36:11.942000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T10:12:52.063000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009899999999999999,
            "end": "2025-08-02T10:36:12.536000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T10:36:11.942000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 47.00618333333333,
            "end": "2025-08-02T11:23:12.907000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T10:36:12.536000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009949999999999999,
            "end": "2025-08-02T11:23:13.504000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T11:23:12.907000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 176.6176,
            "end": "2025-08-02T14:19:50.560000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T11:23:13.504000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.016833333333333332,
            "end": "2025-08-02T14:19:51.570000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T14:19:50.560000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 161.47296666666668,
            "end": "2025-08-02T17:01:19.948000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T14:19:51.570000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009483333333333333,
            "end": "2025-08-02T17:01:20.517000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T17:01:19.948000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 27.849633333333333,
            "end": "2025-08-02T17:29:11.495000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T17:01:20.517000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.00335,
            "end": "2025-08-02T17:29:11.696000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T17:29:11.495000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 75.50588333333333,
            "end": "2025-08-02T18:44:42.049000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T17:29:11.696000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.013433333333333334,
            "end": "2025-08-02T18:44:42.855000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T18:44:42.049000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 124.21266666666666,
            "end": "2025-08-02T20:48:55.615000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T18:44:42.855000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.020116666666666668,
            "end": "2025-08-02T20:48:56.822000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T20:48:55.615000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 26.138883333333336,
            "end": "2025-08-02T21:15:05.155000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T20:48:56.822000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0107,
            "end": "2025-08-02T21:15:05.797000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T21:15:05.155000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 117.69654999999999,
            "end": "2025-08-02T23:12:47.590000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T21:15:05.797000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.010033333333333333,
            "end": "2025-08-02T23:12:48.192000-04:00",
            "mode": "DCP",
            "start": "2025-08-02T23:12:47.590000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 174.38338333333334,
            "end": "2025-08-03T02:07:11.195000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T23:12:48.192000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009983333333333334,
            "end": "2025-08-03T02:07:11.794000-04:00",
            "mode": "DCP",
            "start": "2025-08-03T02:07:11.195000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 69.05891666666666,
            "end": "2025-08-03T03:16:15.329000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T02:07:11.794000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 114.32745,
            "end": "2025-08-03T05:10:34.976000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T03:16:15.329000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.01015,
            "end": "2025-08-03T05:10:35.585000-04:00",
            "mode": "DCP",
            "start": "2025-08-03T05:10:34.976000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 72.74845,
            "end": "2025-08-03T06:23:20.492000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T05:10:35.585000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009983333333333334,
            "end": "2025-08-03T06:23:21.091000-04:00",
            "mode": "DCP",
            "start": "2025-08-03T06:23:20.492000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.5900666666666667,
            "end": "2025-08-03T06:23:56.495000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T06:23:21.091000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.01005,
            "end": "2025-08-03T06:23:57.098000-04:00",
            "mode": "DCP",
            "start": "2025-08-03T06:23:56.495000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 108.69405,
            "end": "2025-08-03T08:12:38.741000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T06:23:57.098000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.010199999999999999,
            "end": "2025-08-03T08:12:39.353000-04:00",
            "mode": "DCP",
            "start": "2025-08-03T08:12:38.741000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 71.18096666666666,
            "end": "2025-08-03T09:23:50.211000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T08:12:39.353000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.010116666666666666,
            "end": "2025-08-03T09:23:50.818000-04:00",
            "mode": "DCP",
            "start": "2025-08-03T09:23:50.211000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 32.83473333333333,
            "end": "2025-08-03T09:56:40.902000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T09:23:50.818000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009966666666666667,
            "end": "2025-08-03T09:56:41.500000-04:00",
            "mode": "DCP",
            "start": "2025-08-03T09:56:40.902000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 182.56995,
            "end": "2025-08-03T12:59:15.697000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T09:56:41.500000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.5098333333333334,
            "end": "2025-08-03T12:59:46.287000-04:00",
            "mode": "ATT",
            "start": "2025-08-03T12:59:15.697000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 3.2115500000000003,
            "end": "2025-08-03T13:02:58.980000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T12:59:46.287000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.5831166666666667,
            "end": "2025-08-03T13:03:33.967000-04:00",
            "mode": "ISC",
            "start": "2025-08-03T13:02:58.980000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 43.68378333333333,
            "end": "2025-08-03T13:47:14.994000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T13:03:33.967000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0006666666666666666,
            "end": "2025-08-03T13:47:15.034000-04:00",
            "mode": "NAV",
            "start": "2025-08-03T13:47:14.994000-04:00",
            "status": "downtime"
          },
          {
            "duration_minutes": 0.24855,
            "end": "2025-08-03T13:47:29.947000-04:00",
            "mode": "INI",
            "start": "2025-08-03T13:47:15.034000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.006583333333333333,
            "end": "2025-08-03T13:47:30.342000-04:00",
            "mode": "IDL",
            "start": "2025-08-03T13:47:29.947000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 1.56725,
            "end": "2025-08-03T13:49:04.377000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T13:47:30.342000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 2.2007833333333333,
            "end": "2025-08-03T13:51:16.424000-04:00",
            "mode": "CTL",
            "start": "2025-08-03T13:49:04.377000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 213.33346666666665,
            "end": "2025-08-03T17:24:36.432000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T13:51:16.424000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.07941666666666666,
            "end": "2025-08-03T17:24:41.197000-04:00",
            "mode": "ISC",
            "start": "2025-08-03T17:24:36.432000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.026783333333333333,
            "end": "2025-08-03T17:24:42.804000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T17:24:41.197000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.06343333333333333,
            "end": "2025-08-03T17:24:46.610000-04:00",
            "mode": "ATT",
            "start": "2025-08-03T17:24:42.804000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 36.89606666666667,
            "end": "2025-08-03T18:01:40.374000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T17:24:46.610000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.032933333333333335,
            "end": "2025-08-03T18:01:42.350000-04:00",
            "mode": "PRK",
            "start": "2025-08-03T18:01:40.374000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 26.92278333333333,
            "end": "2025-08-03T18:28:37.717000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T18:01:42.350000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009949999999999999,
            "end": "2025-08-03T18:28:38.314000-04:00",
            "mode": "DCP",
            "start": "2025-08-03T18:28:37.717000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 353.67775,
            "end": "2025-08-04T00:22:18.979000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T18:28:38.314000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.006683333333333334,
            "end": "2025-08-04T00:22:19.380000-04:00",
            "mode": "DCP",
            "start": "2025-08-04T00:22:18.979000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 72.28468333333333,
            "end": "2025-08-04T01:34:36.461000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T00:22:19.380000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009983333333333334,
            "end": "2025-08-04T01:34:37.060000-04:00",
            "mode": "DCP",
            "start": "2025-08-04T01:34:36.461000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 252.94979999999998,
            "end": "2025-08-04T05:47:34.048000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T01:34:37.060000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.04673333333333333,
            "end": "2025-08-04T05:47:36.852000-04:00",
            "mode": "IDL",
            "start": "2025-08-04T05:47:34.048000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 86.27643333333334,
            "end": "2025-08-04T07:13:53.438000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T05:47:36.852000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.010166666666666666,
            "end": "2025-08-04T07:13:54.048000-04:00",
            "mode": "DCP",
            "start": "2025-08-04T07:13:53.438000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 51.357216666666666,
            "end": "2025-08-04T08:05:15.481000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T07:13:54.048000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0035,
            "end": "2025-08-04T08:05:15.691000-04:00",
            "mode": "DCP",
            "start": "2025-08-04T08:05:15.481000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 64.20191666666666,
            "end": "2025-08-04T09:09:27.806000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T08:05:15.691000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.013566666666666666,
            "end": "2025-08-04T09:09:28.620000-04:00",
            "mode": "DCP",
            "start": "2025-08-04T09:09:27.806000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 150.6713,
            "end": "2025-08-04T11:40:08.898000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T09:09:28.620000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.010199999999999999,
            "end": "2025-08-04T11:40:09.510000-04:00",
            "mode": "DCP",
            "start": "2025-08-04T11:40:08.898000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 5.825266666666667,
            "end": "2025-08-04T11:45:59.026000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T11:40:09.510000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009949999999999999,
            "end": "2025-08-04T11:45:59.623000-04:00",
            "mode": "DCP",
            "start": "2025-08-04T11:45:59.026000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 45.50551666666667,
            "end": "2025-08-04T12:31:29.954000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T11:45:59.623000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.010183333333333332,
            "end": "2025-08-04T12:31:30.565000-04:00",
            "mode": "DCP",
            "start": "2025-08-04T12:31:29.954000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 75.31571666666667,
            "end": "2025-08-04T13:46:49.508000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T12:31:30.565000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.006716666666666667,
            "end": "2025-08-04T13:46:49.911000-04:00",
            "mode": "DCP",
            "start": "2025-08-04T13:46:49.508000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 79.01759999999999,
            "end": "2025-08-04T15:05:50.967000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T13:46:49.911000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0006666666666666666,
            "end": "2025-08-04T15:05:51.007000-04:00",
            "mode": "NAV",
            "start": "2025-08-04T15:05:50.967000-04:00",
            "status": "downtime"
          },
          {
            "duration_minutes": 0.24841666666666665,
            "end": "2025-08-04T15:06:05.912000-04:00",
            "mode": "INI",
            "start": "2025-08-04T15:05:51.007000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 9.086433333333334,
            "end": "2025-08-04T15:15:11.098000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T15:06:05.912000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009766666666666667,
            "end": "2025-08-04T15:15:11.684000-04:00",
            "mode": "DCP",
            "start": "2025-08-04T15:15:11.098000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 238.9372666666667,
            "end": "2025-08-04T19:14:07.920000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T15:15:11.684000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0036,
            "end": "2025-08-04T19:14:08.136000-04:00",
            "mode": "DCP",
            "start": "2025-08-04T19:14:07.920000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 199.86426666666665,
            "end": "2025-08-04T22:33:59.992000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T19:14:08.136000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009816666666666666,
            "end": "2025-08-04T22:34:00.581000-04:00",
            "mode": "DCP",
            "start": "2025-08-04T22:33:59.992000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 110.87743333333333,
            "end": "2025-08-05T00:24:53.227000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T22:34:00.581000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.016983333333333333,
            "end": "2025-08-05T00:24:54.246000-04:00",
            "mode": "DCP",
            "start": "2025-08-05T00:24:53.227000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 235.2128833333333,
            "end": "2025-08-05T04:20:07.019000-04:00",
            "mode": "NOR",
            "start": "2025-08-05T00:24:54.246000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009683333333333332,
            "end": "2025-08-05T04:20:07.600000-04:00",
            "mode": "DCP",
            "start": "2025-08-05T04:20:07.019000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 472.48401666666666,
            "end": "2025-08-05T12:12:36.641000-04:00",
            "mode": "NOR",
            "start": "2025-08-05T04:20:07.600000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009966666666666667,
            "end": "2025-08-05T12:12:37.239000-04:00",
            "mode": "DCP",
            "start": "2025-08-05T12:12:36.641000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 109.86093333333334,
            "end": "2025-08-05T14:02:28.895000-04:00",
            "mode": "NOR",
            "start": "2025-08-05T12:12:37.239000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009949999999999999,
            "end": "2025-08-05T14:02:29.492000-04:00",
            "mode": "DCP",
            "start": "2025-08-05T14:02:28.895000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 116.78011666666666,
            "end": "2025-08-05T15:59:16.299000-04:00",
            "mode": "NOR",
            "start": "2025-08-05T14:02:29.492000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009716666666666667,
            "end": "2025-08-05T15:59:16.882000-04:00",
            "mode": "DCP",
            "start": "2025-08-05T15:59:16.299000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 47.282900000000005,
            "end": "2025-08-05T16:46:33.856000-04:00",
            "mode": "NOR",
            "start": "2025-08-05T15:59:16.882000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.06001666666666667,
            "end": "2025-08-05T16:46:37.457000-04:00",
            "mode": "IDL",
            "start": "2025-08-05T16:46:33.856000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 665.8244833333333,
            "end": "2025-08-06T03:52:26.926000-04:00",
            "mode": "NOR",
            "start": "2025-08-05T16:46:37.457000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0033666666666666667,
            "end": "2025-08-06T03:52:27.128000-04:00",
            "mode": "DCP",
            "start": "2025-08-06T03:52:26.926000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 392.61415,
            "end": "2025-08-06T10:25:03.977000-04:00",
            "mode": "NOR",
            "start": "2025-08-06T03:52:27.128000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009899999999999999,
            "end": "2025-08-06T10:25:04.571000-04:00",
            "mode": "DCP",
            "start": "2025-08-06T10:25:03.977000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 103.05856666666666,
            "end": "2025-08-06T12:08:08.085000-04:00",
            "mode": "NOR",
            "start": "2025-08-06T10:25:04.571000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.00365,
            "end": "2025-08-06T12:08:08.304000-04:00",
            "mode": "DCP",
            "start": "2025-08-06T12:08:08.085000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 19.049066666666665,
            "end": "2025-08-06T12:27:11.248000-04:00",
            "mode": "NOR",
            "start": "2025-08-06T12:08:08.304000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 6.9887,
            "end": "2025-08-06T12:34:10.570000-04:00",
            "mode": "NOR",
            "start": "2025-08-06T12:27:11.248000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 214.50766666666667,
            "end": "2025-08-06T16:08:41.030000-04:00",
            "mode": "NOR",
            "start": "2025-08-06T12:34:10.570000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009916666666666666,
            "end": "2025-08-06T16:08:41.625000-04:00",
            "mode": "DCP",
            "start": "2025-08-06T16:08:41.030000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 133.20235,
            "end": "2025-08-06T18:21:53.766000-04:00",
            "mode": "NOR",
            "start": "2025-08-06T16:08:41.625000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009833333333333333,
            "end": "2025-08-06T18:21:54.356000-04:00",
            "mode": "DCP",
            "start": "2025-08-06T18:21:53.766000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 8.826566666666668,
            "end": "2025-08-06T18:30:43.950000-04:00",
            "mode": "NOR",
            "start": "2025-08-06T18:21:54.356000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009816666666666666,
            "end": "2025-08-06T18:30:44.539000-04:00",
            "mode": "DCP",
            "start": "2025-08-06T18:30:43.950000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 15.495416666666667,
            "end": "2025-08-06T18:46:14.264000-04:00",
            "mode": "NOR",
            "start": "2025-08-06T18:30:44.539000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009916666666666666,
            "end": "2025-08-06T18:46:14.859000-04:00",
            "mode": "DCP",
            "start": "2025-08-06T18:46:14.264000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 48.17361666666667,
            "end": "2025-08-06T19:34:25.276000-04:00",
            "mode": "NOR",
            "start": "2025-08-06T18:46:14.859000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009616666666666666,
            "end": "2025-08-06T19:34:25.853000-04:00",
            "mode": "DCP",
            "start": "2025-08-06T19:34:25.276000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 158.87768333333332,
            "end": "2025-08-06T22:13:18.514000-04:00",
            "mode": "NOR",
            "start": "2025-08-06T19:34:25.853000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.009883333333333333,
            "end": "2025-08-06T22:13:19.107000-04:00",
            "mode": "DCP",
            "start": "2025-08-06T22:13:18.514000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 90.98788333333333,
            "end": "2025-08-06T23:44:18.380000-04:00",
            "mode": "NOR",
            "start": "2025-08-06T22:13:19.107000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.04655,
            "end": "2025-08-06T23:44:21.173000-04:00",
            "mode": "DCP",
            "start": "2025-08-06T23:44:18.380000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 15.63045,
            "end": "2025-08-06T23:59:59-04:00",
            "mode": "NOR",
            "start": "2025-08-06T23:44:21.173000-04:00",
            "status": "uptime"
          }
        ],
        "machine_id": "1",
        "total_minutes": 7704.510866666664,
        "uptime_minutes": 7704.50953333333,
        "uptime_percentage": 99.99998269412093
      },
      {
        "daily_availability": [
          {
            "actual_hours": 0.0,
            "availability_percentage": 0.0,
            "date": "2025-07-31",
            "expected_hours": 23.99972222222222,
            "has_data": false
          },
          {
            "actual_hours": 0.0,
            "availability_percentage": 0.0,
            "date": "2025-08-01",
            "expected_hours": 23.99972222222222,
            "has_data": false
          },
          {
            "actual_hours": 10.579013888888888,
            "availability_percentage": 44.07973471915184,
            "date": "2025-08-02",
            "expected_hours": 23.99972222222222,
            "has_data": true
          },
          {
            "actual_hours": 23.99972222222222,
            "availability_percentage": 100.0,
            "date": "2025-08-03",
            "expected_hours": 23.99972222222222,
            "has_data": true
          },
          {
            "actual_hours": 23.99972222222222,
            "availability_percentage": 100.0,
            "date": "2025-08-04",
            "expected_hours": 23.99972222222222,
            "has_data": true
          },
          {
            "actual_hours": 23.999722222222225,
            "availability_percentage": 100.00000000000003,
            "date": "2025-08-05",
            "expected_hours": 23.99972222222222,
            "has_data": true
          },
          {
            "actual_hours": 23.999722222222218,
            "availability_percentage": 99.99999999999999,
            "date": "2025-08-06",
            "expected_hours": 23.99972222222222,
            "has_data": true
          }
        ],
        "data_coverage_percentage": 63.43999411374689,
        "downtime_minutes": 0.0007,
        "downtime_percentage": 1.0946495225438507e-05,
        "has_data": true,
        "intervals": [
          {
            "duration_minutes": 0.1934,
            "end": "2025-08-02T13:25:26.154000-04:00",
            "mode": "ATT",
            "start": "2025-08-02T13:25:14.550000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 830.82515,
            "end": "2025-08-03T03:16:15.663000-04:00",
            "mode": "NOR",
            "start": "2025-08-02T13:25:26.154000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 583.6394166666666,
            "end": "2025-08-03T12:59:54.028000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T03:16:15.663000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.07646666666666667,
            "end": "2025-08-03T12:59:58.616000-04:00",
            "mode": "ATT",
            "start": "2025-08-03T12:59:54.028000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 47.4182,
            "end": "2025-08-03T13:47:23.708000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T12:59:58.616000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.16590000000000002,
            "end": "2025-08-03T13:47:33.662000-04:00",
            "mode": "INI",
            "start": "2025-08-03T13:47:23.708000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 1488.9335500000002,
            "end": "2025-08-04T14:36:29.675000-04:00",
            "mode": "NOR",
            "start": "2025-08-03T13:47:33.662000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.0007,
            "end": "2025-08-04T14:36:29.717000-04:00",
            "mode": "NAV",
            "start": "2025-08-04T14:36:29.675000-04:00",
            "status": "downtime"
          },
          {
            "duration_minutes": 0.16593333333333332,
            "end": "2025-08-04T14:36:39.673000-04:00",
            "mode": "INI",
            "start": "2025-08-04T14:36:29.717000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 1129.035,
            "end": "2025-08-05T09:25:41.773000-04:00",
            "mode": "NOR",
            "start": "2025-08-04T14:36:39.673000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.166,
            "end": "2025-08-05T09:25:51.733000-04:00",
            "mode": "INI",
            "start": "2025-08-05T09:25:41.773000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 0.027816666666666667,
            "end": "2025-08-05T09:25:53.402000-04:00",
            "mode": "IDL",
            "start": "2025-08-05T09:25:51.733000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 1621.2805999999998,
            "end": "2025-08-06T12:27:10.238000-04:00",
            "mode": "NOR",
            "start": "2025-08-05T09:25:53.402000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 6.994866666666667,
            "end": "2025-08-06T12:34:09.930000-04:00",
            "mode": "NOR",
            "start": "2025-08-06T12:27:10.238000-04:00",
            "status": "uptime"
          },
          {
            "duration_minutes": 685.8178333333333,
            "end": "2025-08-06T23:59:59-04:00",
            "mode": "NOR",
            "start": "2025-08-06T12:34:09.930000-04:00",
            "status": "uptime"
          }
        ],
        "machine_id": "2",
        "total_minutes": 6394.740833333334,
        "uptime_minutes": 6394.740133333335,
        "uptime_percentage": 99.99998905350478
      }
    ],
    "time_range": {
      "end": "2025-08-06T23:59:59-04:00",
      "start": "2025-07-31T00:00:00-04:00",
      "timezone": "America/New_York"
    }
  }
}
"""

data = json.loads(json_data)
machine_metrics = data['tool_results']['machine_metrics']

output_file = 'elevator_timeseries_4995d395-9b4b-4234-a8aa-9938ef5620c6.csv'
csv_columns = ['machine_id', 'start_time', 'end_time', 'mode', 'status', 'duration_minutes']

with open(output_file, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
    writer.writeheader()
    
    for machine in machine_metrics:
        machine_id = machine['machine_id']
        for interval in machine['intervals']:
            row = {
                'machine_id': machine_id,
                'start_time': interval['start'],
                'end_time': interval['end'],
                'mode': interval['mode'],
                'status': interval['status'],
                'duration_minutes': interval['duration_minutes']
            }
            writer.writerow(row)

print(f"Successfully exported data to {output_file}")


