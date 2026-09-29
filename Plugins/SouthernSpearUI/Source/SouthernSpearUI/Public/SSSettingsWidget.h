// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SSSettingsWidget.generated.h"

class UTextBlock;
class UWidget;

/** One option row: label, value, and previous/next buttons. */
UCLASS()
class SSUI_API USSSettingRow : public UObject
{
	GENERATED_BODY()

public:
	UFUNCTION() void Prev() { Step(-1); }
	UFUNCTION() void Next() { Step(+1); }

	void Step(int32 Delta);
	void Refresh();

	UPROPERTY(Transient) TObjectPtr<UTextBlock> ValueText;
	UPROPERTY(Transient) TObjectPtr<UWidget> RowWidget;
	TArray<FText> Options;
	int32 Index = 0;
	TFunction<void(int32)> OnChanged;
};

/**
 * Settings screen (front end and match menu), five tabs: Display (window,
 * resolution, VSync, frame limit, field of view, brightness), Graphics
 * (preset and per-category scalability, render resolution, anti-aliasing,
 * hardware ray tracing, ray-traced shadows, motion blur), Audio, Controls
 * (sensitivity, invert) and Interface (FPS counter, developer messages).
 * Engine settings go through UGameUserSettings on Apply; Southern Spear
 * preferences (FSSUserPrefs) apply immediately. Built in C++.
 */
UCLASS()
class SSUI_API USSSettingsWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual bool Initialize() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	/** Called after Back or Apply closes the screen. */
	TFunction<void()> OnClosed;

	/** Replays the entry animation (call when shown again). */
	void Replay() { Elapsed = 0.f; }

	/** Shows one tab (0 Display, 1 Graphics, 2 Audio, 3 Controls, 4 Interface). */
	void SelectTab(int32 Tab);

private:
	UFUNCTION() void OnApply();
	UFUNCTION() void OnTab0() { SelectTab(0); }
	UFUNCTION() void OnTab1() { SelectTab(1); }
	UFUNCTION() void OnTab2() { SelectTab(2); }
	UFUNCTION() void OnTab3() { SelectTab(3); }
	UFUNCTION() void OnTab4() { SelectTab(4); }

	UFUNCTION() void OnBack();
	UFUNCTION() void OnSetCallsign();

	USSSettingRow* AddRow(class UVerticalBox* Box, const FText& Label, TArray<FText> Options, int32 Current, TFunction<void(int32)> OnChanged);

	UPROPERTY(Transient) TArray<TObjectPtr<USSSettingRow>> Rows;
	UPROPERTY(Transient) TArray<TObjectPtr<UWidget>> Animated;
	UPROPERTY(Transient) TObjectPtr<UWidget> Panel;
	UPROPERTY(Transient) TArray<TObjectPtr<class UVerticalBox>> Pages;
	UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> TabLabels;
	UPROPERTY(Transient) TArray<TObjectPtr<class UBorder>> TabUnderlines;
	UPROPERTY(Transient) TArray<TObjectPtr<USSSettingRow>> QualityRows;
	UPROPERTY(Transient) TObjectPtr<USSSettingRow> PresetRow;
	UPROPERTY(Transient) TObjectPtr<class UEditableTextBox> CallsignBox;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> CallsignFeedback;

	TArray<FIntPoint> Resolutions;
	float Elapsed = 0.f;
};
