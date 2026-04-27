import { shareWithNativeOrCopy } from "./socialShare";

describe("shareWithNativeOrCopy", () => {
  const originalNavigator = global.navigator;

  afterEach(() => {
    Object.defineProperty(global, "navigator", {
      configurable: true,
      value: originalNavigator,
    });
    jest.restoreAllMocks();
  });

  test("copies the dynamic share URL when Web Share API is unavailable", async () => {
    const writeText = jest.fn().mockResolvedValue();
    Object.defineProperty(global, "navigator", {
      configurable: true,
      value: {
      clipboard: { writeText },
      },
    });

    await shareWithNativeOrCopy({
      title: "Caca Radar — Cartagena",
      text: "67 reportes recientes",
      url: "https://cacaradar.es/api/share/location/cartagena",
    });

    expect(writeText).toHaveBeenCalledWith(
      "67 reportes recientes\n\nhttps://cacaradar.es/api/share/location/cartagena"
    );
  });
});
