// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSMenuWidget.generated.h"

class UBorder;
class UButton;
class USSSettingsWidget;
class UTextBlock;
class UWidget;

UENUM()
enum class ESSMenuMode : uint8
{
	/** Title screen: key art, map cards, bot count, settings, quit. */
	FrontEnd,
	/** In match (Esc): resume, settings, leave, quit, controls. The match keeps running. */
	Pause,
};

/**
 * Southern Spear menus, built in C++ in the website style (field-dark plates,
 * brass rules, sand type) with eased entry animations. Set the mode with Setup
 * before AddToViewport.
 */
UCLASS()
class SSUI_API USSMenuWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	void Setup(ESSMenuMode InMode);
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	/** Pause menu: replay the entry animation each time it opens. */
	void Replay() { Elapsed = 0.f; }

	/** Pause menu: close it (and the settings screen), back to game input. */
	void Close() { OnResume(); }

	/** Opens a map in standalone with the chosen number of bots, in game input mode. */
	static void PlayMap(const UObject* Context, const TCHAR* Map);

	static const TCHAR* FrontEndMap;

private:
	UFUNCTION() void OnRedGum();
	UFUNCTION() void OnDryRiver();
	UFUNCTION() void OnSaltbush();
	UFUNCTION() void OnSelatCanal();
	UFUNCTION() void OnBots4();
	UFUNCTION() void OnBots8();
	UFUNCTION() void OnBots12();
	UFUNCTION() void OnSettings();
	UFUNCTION() void OnResume();
	UFUNCTION() void OnMainMenu();
	UFUNCTION() void OnQuit();

	void SetBots(int32 Count);
	UButton* AddHandler(UButton* Button, FName Handler);
	UWidget* Stagger(UWidget* Widget) { Animated.Add(Widget); return Widget; }

	ESSMenuMode Mode = ESSMenuMode::FrontEnd;
	float Elapsed = 0.f;

	UPROPERTY(Transient) TObjectPtr<UWidget> Content;
	UPROPERTY(Transient) TObjectPtr<UWidget> SidePanel;
	UPROPERTY(Transient) TObjectPtr<UBorder> Curtain;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TitleText;
	UPROPERTY(Transient) TArray<TObjectPtr<UWidget>> Animated;
	UPROPERTY(Transient) TArray<TObjectPtr<UButton>> BotButtons;
	UPROPERTY(Transient) TObjectPtr<USSSettingsWidget> Settings;

	/** Bots per match chosen on the front end (kept across menu instances). */
	static int32 SelectedBots;
};
