from datetime import datetime
from config import ParkClientConfig, ParkConfig
from pytz import timezone
import requests


class ParkDataClient:
    """
    ParkDataClient is responsible for fetching, parsing, and processing theme park data from an external API.
    """
    def __init__(self, client_config: ParkClientConfig):
        self.config: ParkClientConfig = client_config
        self.include_single_rider_lines: bool = client_config.include_single_rider_lines
        self.parkConfig: ParkConfig = None
        self.parkData: dict = {}
        self.queueTimesData: dict = {}
        self.parkTz: str = ""
        self.latestUpdate: int = 0
        self.allClosed: bool = True
        self.messageLines: list[str] = []

    async def fetch_park_data(self, parkConfig: ParkConfig):
        """
        Fetch queue times and general park data from the API, parse it into JSON, and store it for processing.
        """
        self.parkData = {}
        self.queueTimesData = {}
        if parkConfig is None or parkConfig.url is None or parkConfig.url == "":
            print("Error: Park config or URL is missing, bailing out...")
            return

        waitTimesUrl = parkConfig.url
        self.parkConfig = parkConfig
        resp = requests.get(waitTimesUrl)
        resp.raise_for_status()
        self.queueTimesData = resp.json()
        
        parkInfoUrl = waitTimesUrl.replace("/queue_times", '')
        parkResp = requests.get(parkInfoUrl)
        parkResp.raise_for_status()
        self.parkData = parkResp.json()


    def process_park_data(self):
        """
        Process the park data and extract relevant information for messaging.
        Message lines are stored in self.messageLines.
        TODO - separate parsing the API response from immediately putting the data into strings for display so we can do more complex analysis and formatting later.
        """
        self.messageLines = []

        if self.parkData is None or len(self.parkData) == 0 or "timezone" not in self.parkData:
            print("Error: Missing park data or tz info in response, bailing out...")
            return
        self.parkTz = self.parkData['timezone']
        self.latestUpdate = 0
        self.allClosed = True

        lands = {land['name']: land for land in self.queueTimesData.get("lands", [])}

        if lands == {}:
            lands[self.config.default_land_key] = {"name": self.config.default_land_key, "rides": self.queueTimesData.get("rides", [])}

        for land_name, land in lands.items():
            if land_name != self.config.default_land_key:
                self.messageLines.append(f"**{land_name}**")
            for ride in land.get("rides", []):
                # optionally skip single rider lines
                if self.config.single_rider_prefix in ride['name'] and not self.config.include_single_rider_lines:
                    continue
                wait = "Closed"
                if ride.get("is_open", False):
                    wait = f"**{ride['wait_time']} min**"
                    self.allClosed = False

                self.messageLines.append(f"{ride['name']}: {wait}")
        
                # Update last updated timestamp, used to make a determination on if the park may or may not be closed
                if "last_updated" in ride:
                    dt = datetime.fromisoformat(ride["last_updated"].replace("Z", "+00:00"))
                    epoch = int(dt.timestamp())
                    if epoch > self.latestUpdate:
                        self.latestUpdate = epoch
                self.messageLines.append("")

    def is_data_stale(self) -> bool:
        """
        Check if the park data is stale.
        Returns True if latestUpdate is older than the stale data threshold or hasn't been set, False otherwise.
        """
        if self.latestUpdate == 0 or self.parkTz == "":
            return True

        utcdt = datetime.now(timezone('UTC'))
        nowEpoch = int(utcdt.timestamp())
        print(f"Latest Update Epoch {self.latestUpdate}, current epoch in UTC: {nowEpoch}")

        return (nowEpoch - self.latestUpdate) >= self.config.stale_data_threshold_seconds

    @property
    def hasData(self) -> bool:
        """
        Returns True if there is processed message data available, False otherwise.
        """
        return self.messageLines != []