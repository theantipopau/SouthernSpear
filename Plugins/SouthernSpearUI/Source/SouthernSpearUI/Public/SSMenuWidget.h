// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSMenuWidget.generated.h"

UENUM()
enum class ESSMenuMode : uint8
{
	/** Title screen: key art, map choice, quit. */
	FrontEnd,
	/** In match (Esc): resume, main menu, quit. The match keeps running. */
	Pause,
};

/**
 * Southern Spear menus, built in C++ in the website style (field-dark plates,
 * brass rules, sand type). Set the mode with Setup before AddToViewport.
 */
UCLASS()
class SSUI_API USSMenuWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	void Setup(ESSMenuMode InMode);

	/** Opens a map in standalone with bots (front end). */
	static void PlayMap(const UObject* Context, const TCHAR* Map);

	/** Map paths used by the front end and the pause menu. */
	static const TCHAR* FrontEndMap;

private:
	UFUNCTION() void OnRedGum();
	UFUNCTION() void OnDryRiver();
	UFUNCTION() void OnResume();
	UFUNCTION() void OnMainMenu();
	UFUNCTION() void OnQuit();

	ESSMenuMode Mode = ESSMenuMode::FrontEnd;
};
