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
 * Settings screen (front end and match menu): display mode, resolution,
 * graphics quality, VSync, frame limit and field of view. Engine settings go
 * through UGameUserSettings on Apply; field of view is a Southern Spear
 * preference (FSSUserPrefs) applied immediately. Built in C++.
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

private:
	UFUNCTION() void OnApply();
	UFUNCTION() void OnBack();

	USSSettingRow* AddRow(class UVerticalBox* Box, const FText& Label, TArray<FText> Options, int32 Current, TFunction<void(int32)> OnChanged);

	UPROPERTY(Transient) TArray<TObjectPtr<USSSettingRow>> Rows;
	UPROPERTY(Transient) TArray<TObjectPtr<UWidget>> Animated;
	UPROPERTY(Transient) TObjectPtr<UWidget> Panel;

	TArray<FIntPoint> Resolutions;
	float Elapsed = 0.f;
};
