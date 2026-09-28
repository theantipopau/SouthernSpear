// Copyright Southern Spear. All Rights Reserved.

#include "SSCompassWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GenericTeamAgentInterface.h"
#include "SSObjectiveActor.h"
#include "SSObjectiveAssaultDirector.h"
#include "SSObjectiveHudModel.h"
#include "SSUIStyle.h"
#include "Styling/CoreStyle.h"
#include "SSFonts.h"

namespace
{
	constexpr float StripWidth = 420.f;
	constexpr float StripHeight = 26.f;
	constexpr float VisibleDegrees = 120.f;  // field shown across the strip
	constexpr int32 LabelStep = 15;
	constexpr int32 CompassMaxMarkers = 6;

	UTextBlock* CompassText(UWidgetTree* Tree, int32 Size, const FLinearColor& Colour)
	{
		UTextBlock* Text = Tree->ConstructWidget<UTextBlock>();
		Text->SetFont(SSFonts::Display(Size));
		Text->SetColorAndOpacity(Colour);
		Text->SetJustification(ETextJustify::Center);
		Text->SetShadowOffset(FVector2D(1.f, 1.f));
		Text->SetShadowColorAndOpacity(SSUIStyle::Ink950(0.8f));
		return Text;
	}

	/** World yaw (Unreal: 0 = +X) to a compass bearing where 0 = north (+X), clockwise. */
	float Bearing(float Yaw) { return FMath::Fmod(Yaw + 360.f, 360.f); }

	/** Signed angle from the view heading to a bearing, -180..180. */
	float Relative(float Target, float Heading) { return FRotator::NormalizeAxis(Target - Heading); }
}

void USSCompassWidget::Setup(ASSObjectiveAssaultDirector* InDirector)
{
	Director = InDirector;
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return;
	}
	UWidgetTree* T = WidgetTree;
	UCanvasPanel* Root = T->ConstructWidget<UCanvasPanel>();
	T->RootWidget = Root;

	// Top centre, alone (the objective panel sits top right under the minimap).
	UVerticalBox* Column = T->ConstructWidget<UVerticalBox>();
	UCanvasPanelSlot* ColumnSlot = Root->AddChildToCanvas(Column);
	ColumnSlot->SetAnchors(FAnchors(0.5f, 0.f));
	ColumnSlot->SetAlignment(FVector2D(0.5f, 0.f));
	ColumnSlot->SetPosition(FVector2D(0.f, 8.f));
	ColumnSlot->SetAutoSize(true);

	UBorder* Plate = T->ConstructWidget<UBorder>();
	Plate->SetBrushColor(SSUIStyle::Ink900(0.35f));
	Plate->SetPadding(FMargin(0.f));
	Column->AddChildToVerticalBox(Plate);
	USizeBox* Size = T->ConstructWidget<USizeBox>();
	Size->SetWidthOverride(StripWidth);
	Size->SetHeightOverride(StripHeight + 30.f);
	Plate->SetContent(Size);
	Strip = T->ConstructWidget<UCanvasPanel>();
	Size->AddChild(Strip);

	for (int32 Deg = 0; Deg < 360; Deg += LabelStep)
	{
		const bool bCardinal = Deg % 90 == 0;
		const bool bInter = Deg % 45 == 0;
		static const TCHAR* Names[] = { TEXT("N"), TEXT("NE"), TEXT("E"), TEXT("SE"), TEXT("S"), TEXT("SW"), TEXT("W"), TEXT("NW") };
		UTextBlock* Label = CompassText(T, bCardinal ? 14 : (bInter ? 11 : 9),
			bCardinal ? SSUIStyle::Brass300() : SSUIStyle::Sage400());
		Label->SetText(FText::FromString(bInter ? Names[Deg / 45] : FString::FromInt(Deg)));
		UCanvasPanelSlot* S = Strip->AddChildToCanvas(Label);
		S->SetAutoSize(true);
		S->SetAlignment(FVector2D(0.5f, 0.f));
		Labels.Add(Label);
	}

	// Centre notch.
	UBorder* Notch = T->ConstructWidget<UBorder>();
	Notch->SetBrushColor(SSUIStyle::Brass500());
	UCanvasPanelSlot* NotchSlot = Strip->AddChildToCanvas(Notch);
	NotchSlot->SetSize(FVector2D(2.f, 8.f));
	NotchSlot->SetPosition(FVector2D(StripWidth * 0.5f - 1.f, 0.f));

	for (int32 Index = 0; Index < CompassMaxMarkers; ++Index)
	{
		UVerticalBox* Box = T->ConstructWidget<UVerticalBox>();
		UBorder* Marker = T->ConstructWidget<UBorder>();
		Marker->SetBrushColor(SSUIStyle::Field800(0.9f));
		Marker->SetPadding(FMargin(5.f, 1.f));
		UTextBlock* Letter = CompassText(T, 11, SSUIStyle::Sand100());
		Marker->SetContent(Letter);
		UVerticalBoxSlot* MarkerSlot = Box->AddChildToVerticalBox(Marker);
		MarkerSlot->SetHorizontalAlignment(HAlign_Center);
		UTextBlock* Distance = CompassText(T, 9, SSUIStyle::Sand100());
		UVerticalBoxSlot* DistanceSlot = Box->AddChildToVerticalBox(Distance);
		DistanceSlot->SetHorizontalAlignment(HAlign_Center);
		UCanvasPanelSlot* S = Strip->AddChildToCanvas(Box);
		S->SetAutoSize(true);
		S->SetAlignment(FVector2D(0.5f, 0.f));
		Box->SetVisibility(ESlateVisibility::Collapsed);
		Markers.Add(Marker);
		MarkerLetters.Add(Letter);
		MarkerDistances.Add(Distance);
	}

	HeadingText = CompassText(T, 10, SSUIStyle::Sand100());
	UVerticalBoxSlot* HeadingSlot = Column->AddChildToVerticalBox(HeadingText);
	HeadingSlot->SetHorizontalAlignment(HAlign_Center);
	HeadingSlot->SetPadding(FMargin(0.f, 2.f, 0.f, 0.f));
}

void USSCompassWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	const APlayerController* Player = GetOwningPlayer();
	const APawn* Pawn = GetOwningPlayerPawn();
	const ASSObjectiveAssaultDirector* Dir = Director.Get();
	if (!Strip || !Player)
	{
		return;
	}
	SetVisibility(Pawn ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	if (!Pawn)
	{
		return;
	}

	const float Heading = Bearing(Player->GetControlRotation().Yaw);
	const float PxPerDeg = StripWidth / VisibleDegrees;
	for (int32 Index = 0; Index < Labels.Num(); ++Index)
	{
		const float Delta = Relative(static_cast<float>(Index * LabelStep), Heading);
		const bool bShown = FMath::Abs(Delta) < VisibleDegrees * 0.5f - 4.f;
		Labels[Index]->SetVisibility(bShown ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		if (bShown)
		{
			Cast<UCanvasPanelSlot>(Labels[Index]->Slot)->SetPosition(FVector2D(StripWidth * 0.5f + Delta * PxPerDeg, 8.f));
			Labels[Index]->SetRenderOpacity(1.f - FMath::Abs(Delta) / (VisibleDegrees * 0.5f) * 0.6f);
		}
	}
	HeadingText->SetText(FText::FromString(FString::Printf(TEXT("%03d"), FMath::RoundToInt(Heading) % 360)));

	if (!Dir)
	{
		return;
	}
	ESSTeamId ViewerTeam = ESSTeamId::None;
	if (const IGenericTeamAgentInterface* Agent = Cast<IGenericTeamAgentInterface>(Player))
	{
		ViewerTeam = Dir->ToTeamId(Agent->GetGenericTeamId());
	}
	const TArray<TObjectPtr<ASSObjectiveActor>>& Objectives = Dir->GetObjectives();
	TArray<FSSObjectiveState> States;
	for (const ASSObjectiveActor* Objective : Objectives)
	{
		States.Add(Objective ? Objective->GetObjectiveState() : FSSObjectiveState());
	}
	FSSObjectiveHudModel Model;
	Model.BuildChips(States, Dir->GetRoundState().ActiveObjectiveIndex, ViewerTeam);

	const FVector Eye = Pawn->GetActorLocation();
	for (int32 Index = 0; Index < Markers.Num(); ++Index)
	{
		UWidget* Box = Markers[Index]->GetParent();
		const ASSObjectiveActor* Objective = Objectives.IsValidIndex(Index) ? Objectives[Index].Get() : nullptr;
		if (!Box || !Objective || !Model.Chips.IsValidIndex(Index))
		{
			if (Box) { Box->SetVisibility(ESlateVisibility::Collapsed); }
			continue;
		}
		const FSSObjectiveHudModel::FChip& Chip = Model.Chips[Index];
		const FVector To = Objective->GetActorLocation() - Eye;
		// Off-strip objectives pin to the nearest edge, so the direction still reads.
		const float Delta = FMath::Clamp(Relative(Bearing(To.Rotation().Yaw), Heading), -VisibleDegrees * 0.5f + 6.f, VisibleDegrees * 0.5f - 6.f);
		Cast<UCanvasPanelSlot>(Box->Slot)->SetPosition(FVector2D(StripWidth * 0.5f + Delta * PxPerDeg, 22.f));
		const FLinearColor Tone = SSUIStyle::ToneColour(Chip.OwnerTone);
		Markers[Index]->SetBrushColor(Chip.bActive ? Tone : SSUIStyle::Field800(0.9f));
		MarkerLetters[Index]->SetText(Chip.Letter);
		MarkerLetters[Index]->SetColorAndOpacity(Chip.bActive ? SSUIStyle::Ink950() : Tone);
		MarkerDistances[Index]->SetText(FText::FromString(FString::Printf(TEXT("%dm"), FMath::RoundToInt(To.Size2D() / 100.f))));
		MarkerDistances[Index]->SetVisibility(Chip.bActive ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		Box->SetVisibility(ESlateVisibility::HitTestInvisible);
		Box->SetRenderOpacity(Chip.bActive ? 1.f : 0.7f);
	}
}
